import os
import io
import logging
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk


@dataclass
class Series:
    x: Deque[float]
    y: Deque[float]


class LiveChartWindow(tk.Toplevel):
    """Janela com gráficos ao vivo para métricas da GPU.

    Lê incrementos de `csv_path` periodicamente e atualiza 4 subplots:
    - gpu_util, memory_util, temp_c, power_w (eixo X: timestamp relativo em segundos).
    
    Observação: Usamos tempo relativo para estabilidade de rendering. Os rótulos do eixo X
    mostram segundos desde o primeiro ponto lido. O CSV é esperado no formato:
        timestamp,gpu_util,memory_util,mem_total_mb,mem_used_mb,temp_c,power_w
    com header dinâmico. O mapeamento de colunas é detectado pelo header.
    """

    def __init__(self, master: tk.Tk, csv_path: str, interval_ms: int = 500, max_points: int = 5000) -> None:
        super().__init__(master)
        self.title("Gráficos ao vivo - GPU")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._csv_path = csv_path
        self._interval_ms = max(100, int(interval_ms))
        self._max_points = max(200, int(max_points))
        self._after_id: Optional[str] = None

        # Estado de leitura do arquivo
        self._fh: Optional[io.TextIOWrapper] = None
        self._file_pos: int = 0
        self._header_map: Dict[str, int] = {}
        self._start_ts: Optional[float] = None

        # Séries
        self._series: Dict[str, Series] = {
            "gpu_util": Series(deque(maxlen=self._max_points), deque(maxlen=self._max_points)),
            "memory_util": Series(deque(maxlen=self._max_points), deque(maxlen=self._max_points)),
            "temp_c": Series(deque(maxlen=self._max_points), deque(maxlen=self._max_points)),
            "power_w": Series(deque(maxlen=self._max_points), deque(maxlen=self._max_points)),
        }

        # UI topo com status
        self._status_var = tk.StringVar(value="Aguardando dados…")
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, textvariable=self._status_var).pack(anchor="w")

        # Área Matplotlib embutida
        try:
            import matplotlib
            matplotlib.use("TkAgg")  # garante backend
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except Exception as e:
            self._status_var.set(f"Falha ao inicializar Matplotlib/TkAgg: {e}")
            logging.exception("TkAgg indisponível")
            return

        self._Figure = Figure  # guardas locais
        self._FigureCanvasTkAgg = FigureCanvasTkAgg

        self._fig = self._Figure(figsize=(8, 6), constrained_layout=True)
        self._axes = [
            self._fig.add_subplot(2, 2, 1),  # gpu_util
            self._fig.add_subplot(2, 2, 2),  # memory_util
            self._fig.add_subplot(2, 2, 3),  # temp_c
            self._fig.add_subplot(2, 2, 4),  # power_w
        ]

        # Config de eixos
        self._axes[0].set_title("Utilização GPU (%)")
        self._axes[1].set_title("Utilização Memória (%)")
        self._axes[2].set_title("Temperatura (°C)")
        self._axes[3].set_title("Potência (W)")
        for ax in self._axes:
            ax.grid(True, alpha=0.3)
            ax.set_xlabel("t (s)")

        # Linhas (animated=True para possível blitting)
        self._lines = {}
        (l1,) = self._axes[0].plot([], [], color="#1f77b4", animated=True)
        (l2,) = self._axes[1].plot([], [], color="#ff7f0e", animated=True)
        (l3,) = self._axes[2].plot([], [], color="#2ca02c", animated=True)
        (l4,) = self._axes[3].plot([], [], color="#d62728", animated=True)
        self._lines = {
            "gpu_util": l1,
            "memory_util": l2,
            "temp_c": l3,
            "power_w": l4,
        }

        # Canvas Tk
        self._canvas = self._FigureCanvasTkAgg(self._fig, master=self)
        self._canvas_widget = self._canvas.get_tk_widget()
        self._canvas_widget.pack(fill="both", expand=True)

        # Blitting state
        self._blit_ready = False
        self._backgrounds: List[Optional[object]] = [None, None, None, None]

        # Desencadeia loop
        self._open_csv_if_available(reset=True)
        self._prime_draw()
        self._schedule_next()

    # API pública para trocar o CSV em tempo real (ex.: ver execução passada)
    def load_csv(self, csv_path: str) -> None:
        self._csv_path = csv_path
        # limpa séries
        for s in self._series.values():
            s.x.clear()
            s.y.clear()
        # reabre arquivo e lê header
        self._open_csv_if_available(reset=True)
        # tenta ler imediatamente o conteúdo já existente
        try:
            self._read_new_lines()
            self._update_plot()
        except Exception:
            logging.exception("Falha ao carregar CSV na janela de gráficos")

    # ================ Infra de leitura CSV ================
    def _open_csv_if_available(self, reset: bool = False) -> None:
        path = self._csv_path
        if not path:
            return
        try:
            if reset or self._fh is None:
                if self._fh:
                    try:
                        self._fh.close()
                    except Exception:
                        pass
                if not os.path.exists(path):
                    self._fh = None
                    self._file_pos = 0
                    self._header_map = {}
                    return
                self._fh = open(path, "r", encoding="utf-8", newline="")
                self._file_pos = 0
                self._header_map = {}
                self._read_header()
            else:
                # Detecta truncamento/rotação
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
                if size < self._file_pos:
                    logging.info("CSV foi truncado/rotacionado. Reinicializando leitura…")
                    self._fh.close()  # type: ignore[union-attr]
                    self._fh = None
                    self._file_pos = 0
                    self._header_map = {}
                    self._open_csv_if_available(reset=True)
        except Exception:
            logging.exception("Falha ao abrir CSV")

    def _read_header(self) -> None:
        if not self._fh:
            return
        # Lê primeira linha como header
        pos0 = self._fh.tell()
        line = self._fh.readline()
        if not line:
            # arquivo vazio até agora
            self._fh.seek(pos0)
            self._file_pos = pos0
            return
        header = [h.strip().lower() for h in line.strip().split(",")]
        idx_map: Dict[str, int] = {}
        for i, name in enumerate(header):
            idx_map[name] = i
        # Campos de interesse
        needed = ["timestamp", "gpu_util", "memory_util", "temp_c", "power_w"]
        missing = [k for k in needed if k not in idx_map]
        if missing:
            logging.warning("Header CSV sem colunas esperadas: faltando %s", ", ".join(missing))
        self._header_map = idx_map
        self._file_pos = self._fh.tell()

    def _read_new_lines(self) -> None:
        if not self._fh:
            return
        self._fh.seek(self._file_pos)
        while True:
            pos_before = self._fh.tell()
            line = self._fh.readline()
            if not line:
                self._fh.seek(pos_before)
                break
            if not line.endswith("\n"):
                # linha parcial ainda sendo escrita, volta e espera próxima rodada
                self._fh.seek(pos_before)
                break
            self._file_pos = self._fh.tell()
            self._process_line(line.rstrip("\n"))

    def _process_line(self, line: str) -> None:
        if not self._header_map:
            # tenta reler header se aparecer de repente
            self._read_header()
            if not self._header_map:
                return
        parts = [p.strip() for p in line.split(",")]
        # timestamp como string; converte para t relativo (s)
        try:
            ts_str = parts[self._header_map.get("timestamp", 0)]
        except Exception:
            return
        # usa contagem de amostras como tempo relativo quando não há timestamp numérico
        t_rel = self._estimate_t_rel()
        # Demais colunas
        for key in ("gpu_util", "memory_util", "temp_c", "power_w"):
            idx = self._header_map.get(key)
            if idx is None or idx >= len(parts):
                continue
            try:
                val = float(parts[idx])
            except ValueError:
                continue
            s = self._series[key]
            s.x.append(t_rel)
            s.y.append(val)

    def _estimate_t_rel(self) -> float:
        # t relativo = número de pontos já coletados do eixo gpu_util (qualquer série serve)
        s = self._series["gpu_util"]
        return float(len(s.x))

    # ================ Atualização de UI/plot ================
    def _prime_draw(self) -> None:
        try:
            self._canvas.draw()
            # Captura backgrounds para blitting
            renderer = self._canvas.get_renderer()
            for i, ax in enumerate(self._axes):
                self._backgrounds[i] = renderer.copy_from_bbox(ax.bbox)
            self._blit_ready = True
        except Exception:
            # Fallback silencioso; usaremos draw_idle
            self._blit_ready = False

    def _update_plot(self) -> None:
        # Atualiza dados das linhas
        for key, line in self._lines.items():
            s = self._series[key]
            line.set_data(list(s.x), list(s.y))
            # auto-scale y
            ax = self._axes[list(self._lines.keys()).index(key)]
            ax.relim()
            ax.autoscale_view(scalex=True, scaley=True)
        # Ajusta limites do eixo X para mostrar janela inteira
        max_len = max((len(s.x) for s in self._series.values()), default=0)
        if max_len > 0:
            x_min = max(0, max_len - self._max_points)
            x_max = max_len
            for ax in self._axes:
                ax.set_xlim(x_min, x_max)

        if self._blit_ready:
            try:
                renderer = self._canvas.get_renderer()
                for i, ax in enumerate(self._axes):
                    # restaura background
                    if self._backgrounds[i] is not None:
                        renderer.restore_region(self._backgrounds[i])
                    # desenha artistas do eixo
                    for line in ax.lines:
                        ax.draw_artist(line)
                    # blit por eixo
                    self._canvas.blit(ax.bbox)
                self._canvas.flush_events()
                return
            except Exception:
                # Desabilita blit se falhar
                logging.info("Blitting indisponível/instável; usando redraw completo")
                self._blit_ready = False

        # Fallback: redesenha tudo de forma leve
        self._canvas.draw_idle()

    def _tick(self) -> None:
        try:
            self._open_csv_if_available()
            if self._fh is None:
                self._status_var.set("Aguardando dados… (arquivo não encontrado)")
            else:
                self._read_new_lines()
                total = max((len(s.x) for s in self._series.values()), default=0)
                self._status_var.set(f"Amostras: {total}")
                self._update_plot()
        except Exception:
            logging.exception("Erro no ciclo de atualização")
        finally:
            self._schedule_next()

    def _schedule_next(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.after(self._interval_ms, self._tick)

    # ================ Encerramento ================
    def _on_close(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        try:
            if self._fh:
                self._fh.close()
        except Exception:
            pass
        try:
            # limpa figure explicitamente
            if hasattr(self, "_fig"):
                self._fig.clf()
        except Exception:
            pass
        self.destroy()
