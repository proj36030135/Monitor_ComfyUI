import os
import sys
import threading
import time
import subprocess
import logging
from pathlib import Path
from tkinter import Tk, StringVar, IntVar, BooleanVar, filedialog, messagebox
from tkinter import ttk
from .logging_utils import setup_logging
from .live_chart import LiveChartWindow


DEFAULT_INTERVALO = 2
DEFAULT_DURACAO = 0
DEFAULT_GPU_INDEX = ""
DEFAULT_COLUNAS = (
    "utilization.gpu,utilization.memory,memory.total,memory.used,temperature.gpu,power.draw"
)
DEFAULT_CSV_PATH = os.path.join(".", "logs", "gpu_log.csv")


class NvidiaSmiCollector:
    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self._stop_event = threading.Event()
        self._timer_thread: threading.Thread | None = None

    @staticmethod
    def _normalize_field_name(field: str) -> str:
        mapping = {
            "utilization.gpu": "gpu_util",
            "utilization.memory": "memory_util",
            "memory.total": "mem_total_mb",
            "memory.used": "mem_used_mb",
            "temperature.gpu": "temp_c",
            "power.draw": "power_w",
        }
        lf = field.strip().lower()
        if lf in mapping:
            return mapping[lf]
        # Fallback: substituir caracteres inválidos
        safe = "".join(ch if ch.isalnum() or ch in ("_",) else "_" for ch in lf.replace(".", "_"))
        return safe.strip("_") or "col"

    def is_nvidia_smi_available(self) -> bool:
        try:
            subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, check=True)
            return True
        except Exception:
            return False

    def start(
        self,
        intervalo_seg: int,
        duracao_seg: int,
        gpu_index: str,
        colunas_query: str,
        csv_path: str,
        overwrite: bool,
    ) -> None:
        if self.process is not None:
            raise RuntimeError("Coleta já está em execução.")

        if not self.is_nvidia_smi_available():
            raise RuntimeError(
                "'nvidia-smi' não encontrado. Verifique a instalação do driver NVIDIA e o PATH."
            )

        Path(os.path.dirname(csv_path) or ".").mkdir(parents=True, exist_ok=True)

        # Normaliza colunas: remove 'timestamp' se informado por engano (sempre geramos timestamp próprio)
        cols = [c.strip() for c in colunas_query.split(",") if c.strip()]
        cols = [c for c in cols if c.lower() != "timestamp"]
        colunas_norm = ",".join(cols)

        # Construção segura do comando
        cmd: list[str] = [
            "nvidia-smi",
            f"--query-gpu={colunas_norm}",
            "--format=csv,noheader,nounits",
        ]
        if intervalo_seg and intervalo_seg > 0:
            cmd.extend(["-l", str(intervalo_seg)])
        if gpu_index:
            cmd.extend(["-i", str(gpu_index)])

        # Arquivo de saída
        file_exists = os.path.exists(csv_path)
        mode = "w" if overwrite else "a"
        write_header = (mode == "w") or (not file_exists)
        header_cols = [self._normalize_field_name(c) for c in cols]
        header = ",".join(["timestamp", *header_cols]) + "\n"

        # Inicia processo
        self._stop_event.clear()
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        def run_reader() -> None:
            start_time = time.time()
            with open(csv_path, mode, encoding="utf-8", newline="") as f:
                if write_header:
                    f.write(header)
                if not self.process or not self.process.stdout:
                    return
                for line in self.process.stdout:
                    if self._stop_event.is_set():
                        break
                    line = line.strip()
                    if not line:
                        continue
                    # A saída já vem sem header e sem units; apenas prepend do timestamp ISO
                    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
                    # Normalização simples de separadores e espaços
                    norm = ",".join([p.strip() for p in line.split(",")])
                    try:
                        f.write(f"{ts},{norm}\n")
                        logging.info("sample written: %s", f"{ts},{norm}")
                    except Exception:
                        # Falha de IO: tenta continuar
                        logging.exception("Falha ao escrever linha no CSV")

                    if duracao_seg and duracao_seg > 0:
                        if time.time() - start_time >= duracao_seg:
                            self.stop()
                            break

        threading.Thread(target=run_reader, daemon=True).start()

    def stop(self) -> None:
        self._stop_event.set()
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except Exception:
                pass
            finally:
                self.process = None


class App(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GPU Monitor Collector")
        self.geometry("700x360")
        self.resizable(False, False)

        self.intervalo_var = IntVar(value=DEFAULT_INTERVALO)
        self.duracao_var = IntVar(value=DEFAULT_DURACAO)
        self.gpu_index_var = StringVar(value=DEFAULT_GPU_INDEX)
        self.colunas_var = StringVar(value=DEFAULT_COLUNAS)
        self.csv_path_var = StringVar(value=DEFAULT_CSV_PATH)
        self.overwrite_var = BooleanVar(value=False)

        self.collector = NvidiaSmiCollector()
        self._chart_window: LiveChartWindow | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # Linha 1
        ttk.Label(frm, text="Intervalo (s)").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.intervalo_var, width=10).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Duração (s, 0=ilimitado)").grid(row=0, column=2, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.duracao_var, width=14).grid(row=0, column=3, sticky="w", **pad)

        # Linha 2
        ttk.Label(frm, text="GPU Index (opcional)").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.gpu_index_var, width=10).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(frm, text="CSV Path").grid(row=1, column=2, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.csv_path_var, width=40).grid(row=1, column=3, sticky="w", **pad)
        ttk.Button(frm, text="Escolher...", command=self._choose_csv).grid(row=1, column=4, sticky="w", **pad)

        # Linha 3
        ttk.Label(frm, text="Colunas (query)").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.colunas_var, width=70).grid(row=2, column=1, columnspan=4, sticky="w", **pad)

        # Linha 4
        ttk.Checkbutton(frm, text="Sobrescrever arquivo", variable=self.overwrite_var).grid(row=3, column=0, sticky="w", **pad)

        # Linha 5 - Botões
        ttk.Button(frm, text="Iniciar", command=self._on_start).grid(row=4, column=0, **pad)
        ttk.Button(frm, text="Parar", command=self._on_stop).grid(row=4, column=1, **pad)
        ttk.Button(frm, text="Abrir Pasta", command=self._open_folder).grid(row=4, column=2, **pad)
        ttk.Button(frm, text="Abrir Grafico", command=self._open_chart).grid(row=4, column=3, **pad)
        ttk.Button(frm, text="Ver Execucao...", command=self._open_past_execution).grid(row=4, column=4, **pad)

        # Status
        self.status_var = StringVar(value="Pronto")
        ttk.Label(frm, textvariable=self.status_var).grid(row=5, column=0, columnspan=5, sticky="w", **pad)

        for i in range(5):
            frm.grid_columnconfigure(i, weight=1)

    def _choose_csv(self) -> None:
        target = filedialog.asksaveasfilename(
            title="Salvar CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=os.path.basename(self.csv_path_var.get()),
        )
        if target:
            self.csv_path_var.set(target)

    def _on_start(self) -> None:
        try:
            intervalo = max(1, int(self.intervalo_var.get()))
            duracao = max(0, int(self.duracao_var.get()))
            gpu_idx = self.gpu_index_var.get().strip()
            colunas = self.colunas_var.get().strip()
            base_path = self.csv_path_var.get().strip() or DEFAULT_CSV_PATH
            csv_path = self._make_session_csv_path(base_path, intervalo_ms=intervalo * 1000)
            self.csv_path_var.set(csv_path)
            overwrite = True

            self.collector.start(
                intervalo_seg=intervalo,
                duracao_seg=duracao,
                gpu_index=gpu_idx,
                colunas_query=colunas,
                csv_path=csv_path,
                overwrite=overwrite,
            )
            self.status_var.set("Coleta em execução…")
            logging.info("Coleta iniciada: intervalo=%s duracao=%s gpu_index=%s csv_path=%s overwrite=%s", intervalo, duracao, gpu_idx, csv_path, overwrite)
            self.status_var.set(f"Coleta em execucao. CSV: {os.path.basename(csv_path)}")
            self._open_chart()
        except Exception as e:
            messagebox.showerror("Erro ao iniciar", str(e))
            logging.exception("Erro ao iniciar coleta")

    def _on_stop(self) -> None:
        try:
            self.collector.stop()
            self.status_var.set("Coleta parada")
            logging.info("Coleta parada pelo usuário")
        except Exception as e:
            messagebox.showerror("Erro ao parar", str(e))
            logging.exception("Erro ao parar coleta")

    def _open_chart(self) -> None:
        try:
            csv_path = self.csv_path_var.get().strip() or DEFAULT_CSV_PATH
            if self._chart_window and self._chart_window.winfo_exists():
                self._chart_window.load_csv(csv_path)
                self._chart_window.deiconify()
                self._chart_window.lift()
                self._chart_window.focus_force()
                return
            self._chart_window = LiveChartWindow(self, csv_path=csv_path, interval_ms=500, max_points=5000)
        except Exception as e:
            messagebox.showerror("Erro ao abrir grafico", str(e))
            logging.exception("Falha ao abrir janela de graficos")

    def _open_past_execution(self) -> None:
        try:
            path = filedialog.askopenfilename(
                title="Selecionar CSV de execucao passada",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=os.path.abspath(os.path.dirname(self.csv_path_var.get()) or "."),
            )
            if not path:
                return
            self.csv_path_var.set(path)
            if self._chart_window and self._chart_window.winfo_exists():
                self._chart_window.load_csv(path)
                self._chart_window.deiconify()
                self._chart_window.lift()
                self._chart_window.focus_force()
            else:
                self._chart_window = LiveChartWindow(self, csv_path=path, interval_ms=500, max_points=5000)
        except Exception as e:
            messagebox.showerror("Erro ao abrir execucao passada", str(e))
            logging.exception("Falha ao abrir execucao passada")

    def _make_session_csv_path(self, base_path: str, intervalo_ms: int) -> str:
        base_dir = os.path.dirname(base_path) or "."
        os.makedirs(base_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        fname = f"gpu_log_{ts}_i{intervalo_ms}.csv"
        return os.path.join(base_dir, fname)

    def _open_folder(self) -> None:
        path = os.path.abspath(os.path.dirname(self.csv_path_var.get()) or ".")
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])


def main() -> None:
    setup_logging()
    logging.info("Aplicação iniciada")
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()



