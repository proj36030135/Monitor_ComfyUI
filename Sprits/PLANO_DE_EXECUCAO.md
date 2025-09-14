# Plano de Execução — GPU Monitor (nvidia-smi → CSV + HTML/Chart.js)

## 1) Visão Geral

Objetivo: coletar métricas de GPU via `nvidia-smi` em intervalo configurável e gravar em CSV; visualizar localmente em uma página HTML estática com Chart.js, sem servidor.

Entregáveis do MVP:
- Coletor Python com UI mínima (Windows), gravação CSV com cabeçalho normalizado, controles Iniciar/Parar e sobrescrever/append.
- Visualizador HTML estático com leitura de CSV (FileReader), gráficos de linha (Chart.js) para séries selecionáveis e escala de tempo no eixo X.

Premissas: operação local, sem rede; Windows 10/11; Python 3.10+; driver NVIDIA com `nvidia-smi` presente no PATH.

---

## 2) Validação do PRD

### 2.1 Escopo (Incluído/Excluído)
- Incluído: coletor Python + página HTML estática. OK — viável e alinhado ao MVP.
- Excluído (MVP): streaming em tempo real, dashboards persistentes, CPU/RAM. OK — não impacta arquitetura proposta.

### 2.2 Usuários & Usos
- Uso primário: acompanhar gargalos do ComfyUI ao longo do tempo (utilização, VRAM, temperatura, potência). OK — séries mapeadas no CSV e no gráfico.

### 2.3 Requisitos Funcionais — Coletor (4.1)
- Parâmetros: `intervalo_seg` (>=1, padrão 2), `duracao_seg` (0 = até parar), `gpu_index` (opcional, mapeado para `-i`), `csv_path`, `colunas_query` (customizável). OK — implementado na UI mínima.
- Comando base: `nvidia-smi --query-gpu=... --format=csv -l <intervalo>` (+ `-i <gpu_index>` quando definido). OK — com opção recomendada `--format=csv,noheader,nounits` para padronizar parsing e o app escrever o cabeçalho normalizado.
- Escrita CSV: cabeçalho fixo e normalizado; append por padrão; opção “Sobrescrever”. OK — previsto.
- Controles: Iniciar/Parar (encerra subprocesso), Abrir pasta. OK — previsto.
- Validações/erros: checar `nvidia-smi` no start; mensagens amigáveis; ignorar ruídos; log em `collector.log`. OK — previsto.

Observação técnica: `duracao_seg` será controlado pelo próprio coletor (timer) encerrando o subprocesso; `nvidia-smi` não oferece duração nativa.

### 2.4 Requisitos Funcionais — Visualizador (4.2)
- Carregamento via `<input type="file">` + `FileReader.readAsText`. OK — sem servidor.
- Gráficos: Chart.js via CDN; múltiplas séries ativáveis (checkbox); linha do tempo. OK — usar escala `timeseries` e plugin de decimação para performance.
- Séries mínimas: GPU Util (%), VRAM Used (MB), Temp (°C), Power (W). OK — mapeadas do CSV padrão.
- UI mínima: seleção de CSV; lista de colunas detectadas; checkboxes; legenda; eixo X temporal. OK — previsto.
- Estilo: CSS leve inspirado no shadcn/ui. OK — tema leve com tokens de cor e radius.

### 2.5 Esquema de Dados (CSV) (5)
- Cabeçalho padrão: `timestamp,gpu_util,memory_util,mem_total_mb,mem_used_mb,temp_c,power_w`. OK — produzido pelo app (mesmo usando `--format=csv,noheader,nounits`).
- Tipos: timestamp ISO-8601 ou string bruta; demais numéricos. OK — viewer normaliza e converte números.

### 2.6 Requisitos Não-Funcionais (6)
- Plataforma: Windows 10/11; Python 3.10+; `nvidia-smi`. OK — suportado.
- Desempenho: amostragem padrão 2s (1–10s). OK — parâmetro validado.
- Tolerância a falhas: permite retomar e continuar append. OK — garantido pelo modo append e checagem de cabeçalho.
- Privacidade: local; página HTML sem rede. OK — sem fetch externo (CDN apenas para libs públicas, opcionável via download offline).

### 2.7 Critérios de Aceite (8)
- A1: Intervalo=2s e duração=60s → ~30 linhas. OK — timer de duração atende.
- A2: CSV abre e exibe ao menos 2 séries simultâneas. OK — datasets múltiplos.
- A3: Alterar `colunas_query` reflete no cabeçalho e viewer lista novas colunas. OK — detecção dinâmica.
- A4: Botão Parar encerra em ≤2s; sem handle preso. OK — kill do subprocesso com timeout e fallback.
- A5: CSV 10k linhas responsivo (zoom/pan fluido). OK — habilitar decimação (LTTB) no Chart.js e, opcionalmente, plugin de zoom.

### 2.8 Riscos & Mitigação (9)
- `nvidia-smi` indisponível: checagem no start e instruções. OK.
- CSV grande: decimação automática e/ou downsampling simples; orientação a fatiar períodos. OK.
- Layout/unidades: usar `nounits` e cabeçalho normalizado para evitar parsing de unidades/locale. OK.

Conclusão: PRD é consistente e exequível no escopo proposto. Pontos críticos mitigados (performance e robustez do coletor/parada limpa).

---

## 3) Arquitetura & Design

### 3.1 Coletor (Python)
- UI: Tkinter minimalista (Windows) com campos: intervalo, duração, gpu_index, colunas_query, csv_path [+ checkbox Sobrescrever]; botões: Iniciar, Parar, Abrir Pasta.
- Execução: `subprocess.Popen([...])` com construção de comando segura; `-l <intervalo>` e `-i <gpu_index>` quando definido.
- Duração: thread/timer que encerra o processo aos `duracao_seg` (se > 0) ou responde ao Parar.
- Escrita CSV: abrir arquivo conforme modo (w/append); escrever cabeçalho normalizado quando criar ou quando “Sobrescrever”; validar consistência do cabeçalho se append.
- Resiliência: leitura de stdout linha a linha; descartar linhas vazias/ruído; logar parsing em `collector.log` (rotacionável simples por tamanho).
- UX: estado da coleta, contagem de amostras, caminho do arquivo.

Campos default:
- `intervalo_seg`: 2  | `duracao_seg`: 0  | `gpu_index`: vazio  | `colunas_query`: `timestamp,utilization.gpu,utilization.memory,memory.total,memory.used,temperature.gpu,power.draw`  | `csv_path`: `./logs/gpu_log.csv`.

### 3.2 Visualizador (HTML estático)
- Estrutura: `index.html` com `<input type="file">`; parser CSV em JS; Chart.js v4 via CDN; checkboxes por coluna.
- Escala temporal: `scales.x.type = 'timeseries'` (dispensa adapter externo para ISO-8601 simples). `spanGaps` configurado para lidar com lacunas.
- Performance: habilitar `options.plugins.decimation = { enabled: true, algorithm: 'lttb', samples: 1000 }` (ou ajuste conforme tamanho); `interaction.mode = 'nearest'`.
- Interação: checkboxes para alternar séries; legenda ativa; opcional `chartjs-plugin-zoom` (zoom com roda/pinch e pan) se necessário.
- Estilo: CSS leve com tokens (cores, radius, spacing) inspirado no shadcn/ui.

### 3.3 Cabeçalho normalizado (CSV)
`timestamp,gpu_util,memory_util,mem_total_mb,mem_used_mb,temp_c,power_w`

Mapeamento recomendado de `--query-gpu` com `--format=csv,noheader,nounits`:
- `timestamp` → `timestamp`
- `utilization.gpu` → `gpu_util`
- `utilization.memory` → `memory_util`
- `memory.total` → `mem_total_mb`
- `memory.used` → `mem_used_mb`
- `temperature.gpu` → `temp_c`
- `power.draw` → `power_w`

---

## 4) Decisões Técnicas
- `--format=csv,noheader,nounits`: simplifica parsing; o app escreve cabeçalho normalizado.
- Encerramento limpo: enviar `terminate()` e, se necessário, `kill()` com timeout de 2s para cumprir A4.
- UI Tkinter: padrão nativo no Windows, sem dependências extras.
- Chart.js `timeseries` no eixo X: suporta datas ISO e oferece boa performance; `spanGaps` para buracos.
- Decimação (LTTB) habilitada: garante responsividade com 10k+ pontos.
- Zoom/Pan: opcional com `chartjs-plugin-zoom` se desejar navegação mais fluida; manter desativado por padrão e habilitar via toggle.

---

## 5) Testes & Aceite (ligação com A1–A5)
- A1: Coletar 60s a 2s → validar ~30 linhas no CSV; checar cabeçalho e consistência de colunas.
- A2: Abrir CSV no Visualizador → exibir pelo menos 2 séries simultâneas; alternar checkboxes.
- A3: Alterar `colunas_query` (ex.: incluir `clocks.gr`) → cabeçalho do CSV muda; viewer lista coluna extra.
- A4: Clicar Parar durante coleta → término em ≤2s; arquivo liberado (renomear/mover sem erro).
- A5: Carregar CSV com 10k linhas → verificar fluidez ao alternar séries e ao pan/zoom (se habilitado) com decimação ativa.

---

## 6) Riscos & Mitigações
- `nvidia-smi` fora do PATH: checar no start (`nvidia-smi -L`); exibir instruções para instalar/atualizar driver.
- Permissões/gravação em `csv_path`: criar pasta `./logs/` automaticamente; mensagens claras em caso de erro de IO.
- Locales/decimais: usar `nounits`; substituir vírgula por ponto no parser (se necessário) antes de converter para número no viewer.
- CSV gigantesco: decimação LTTB e limite configurável de amostras; orientação a dividir por períodos no coletor (um arquivo por job).
- Encerramento do processo: tratamento de sinais e timeout; garantir liberação de handles antes de fechar UI.

---

## 7) Plano de Implementação — 3 Sprints

### Sprint 1 — Coletor Python (5 dias úteis)
Escopo:
- UI Tkinter com parâmetros: intervalo, duração, gpu_index, colunas_query, csv_path, [x] Sobrescrever.
- Execução `nvidia-smi` em loop; escrita CSV com cabeçalho normalizado; modos append/overwrite.
- Controles Iniciar/Parar/Abrir pasta; checagem de `nvidia-smi`; logging básico.

Critérios de aceite:
- Executar coleta 60s/2s gerando ~30 linhas (A1) com cabeçalho correto.
- Parar encerra em ≤2s sem handle preso (A4).

Riscos:
- PATH do `nvidia-smi`; tratativa e instruções na UI.

Entregáveis:
- `collector/` (código Python), `logs/` (criada automaticamente), `collector.log`, README rápido.

### Sprint 2 — Visualizador HTML + Chart.js (4 dias úteis)
Escopo:
- Página estática com `<input type="file">`, parsing CSV e detecção de colunas.
- Gráfico de linhas com `timeseries` no eixo X; múltiplas séries com checkboxes; legenda.
- Estilo CSS leve inspirado no shadcn/ui; layout responsivo simples.

Critérios de aceite:
- Abrir CSV do Sprint 1 e exibir ao menos 2 séries simultâneas (A2).
- Detecção de colunas novas ao mudar o cabeçalho (A3).

Riscos:
- Parsing de CSV com valores vazios; sanitização e feedback na UI.

Entregáveis:
- `viewer/index.html`, `viewer/styles.css`, `viewer/README.md`.

### Sprint 3 — Performance, Robustez e Documentação (3 dias úteis)
Escopo:
- Habilitar decimação (LTTB) no Chart.js; opção de amostrar N pontos.
- Melhorias de UX: estados de loading/erro; instruções claras.
- Documentação completa de uso; script utilitário para abrir viewer; ajustes finais.

Critérios de aceite:
- CSV com 10k linhas permanece fluido (A5).
- Documentação cobrindo A1–A5 (passos de verificação).

Riscos:
- Variedade de layouts de CSV; validar fallback e ignorar colunas não numéricas.

Entregáveis:
- Ajustes no `viewer/index.html`; `DOCS.md` cobrindo instalação/uso/testes.

---

## 8) Referências (Context7/Chart.js)
- Chart.js — Time scale com linha do tempo: [Time Scale Line Chart](https://github.com/chartjs/chart.js/blob/master/docs/samples/scales/time-line.md)
- Chart.js — `spanGaps` e ticks maiores em eixo de tempo: [Time Max Span](https://github.com/chartjs/chart.js/blob/master/docs/samples/scales/time-max-span.md)
- Chart.js — Escala `timeseries` (recomendada para datas ISO): [Timeseries Axis](https://github.com/chartjs/chart.js/blob/master/docs/axes/cartesian/timeseries.md)
- Chart.js — Ajuste de step/ticks (controle visual do eixo Y): [Linear Step Size](https://github.com/chartjs/chart.js/blob/master/docs/samples/scales/linear-step-size.md)
- Chart.js — Exemplos de configuração e performance (decimação LTTB está disponível na v3+): ver docs de plugins e opções de `decimation` em Chart.js.

Observação: para zoom/pan opcional, avaliar `chartjs-plugin-zoom` (CDN), mantendo desabilitado por padrão no MVP para simplicidade.

---

## 9) Próximos Passos
1) Implementar Sprint 1 (coletor) e validar A1/A4.
2) Implementar Sprint 2 (viewer) e validar A2/A3.
3) Implementar Sprint 3 (performance/doc) e validar A5.
4) Opcional: empacotar coletor com PyInstaller para distribuição.


