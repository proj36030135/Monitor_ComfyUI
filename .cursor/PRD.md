PRD — GPU Monitor (nvidia-smi → CSV + HTML/Chart.js)
1) Objetivo

Coletar métricas de GPU via nvidia-smi em intervalo configurável e gravar em CSV, com uma página HTML simples que carrega esse CSV localmente e exibe gráficos interativos (line charts). A coleta usa o modo --query-gpu em formato CSV com loop em segundos; a visualização usa Chart.js via CDN e leitura de arquivo local com FileReader. 


2) Escopo

Incluído

Script Python com UI de parametrização (mínima) para rodar nvidia-smi e gravar CSV.

Página HTML estática que lê um CSV escolhido pelo usuário (input file) e plota gráficos com Chart.js.

Sem servidor, sem banco — apenas arquivos locais.

Excluído (MVP)

Streaming em tempo real pelo navegador (SSE/WebSocket).

Dashboards persistentes (Grafana/Netdata).

Autocoleta de CPU/RAM (apenas GPU no MVP).

3) Usuários & usos

Você/Dev local: verificar gargalos durante jobs do ComfyUI; conferir utilização, VRAM usada, temperatura e potência ao longo do tempo.

4) Requisitos funcionais
4.1 Coletor (Python)

Parâmetros na UI (janela simples):

intervalo_seg (int, padrão 2s, mínimo 1s).

duracao_seg (int; 0 = rodar até parar).

gpu_index (string opcional, ex.: “0”; passa como -i no nvidia-smi). 
developer.download.nvidia.com

csv_path (ex.: ./logs/gpu_log.csv).

colunas_query (string com campos --query-gpu=…; default sugerido abaixo). 
NVIDIA Docs

Comando base:
nvidia-smi --query-gpu=timestamp,utilization.gpu,utilization.memory,memory.total,memory.used,temperature.gpu,power.draw --format=csv -l <intervalo>
(usar -i <gpu_index> quando definido). 
NVIDIA Docs
+1

Escrita de CSV:

Cabeçalho explícito definido pelo app (nomes normalizados, p. ex. timestamp,gpu_util,memory_util,mem_total_mb,mem_used_mb,temp_c,power_w).

Append no arquivo existente; opção “Sobrescrever” (checkbox).

Controles: Iniciar, Parar (encerra o subprocesso), Abrir pasta de logs.

Validações/erros:

Exibir erro amigável se nvidia-smi não estiver disponível (o utilitário vem com os drivers NVIDIA). 
NVIDIA Docs

Ignorar linhas inválidas/ruído do stdout, logar em collector.log.

4.2 Visualizador (HTML estático)

Carregamento de arquivo: <input type="file"> abre um CSV local; leitura com FileReader.readAsText (sem servidor). 
MDN Web Docs
+1

Gráficos: Chart.js via CDN; gráfico de linha com múltiplas séries selecionáveis (checkbox). 
chartjs.org
+1

Séries mínimas:

GPU Util (%)

VRAM Used (MB)

Temp (°C)

Power (W)

UI mínima:

Campo para escolher CSV; lista de colunas detectadas; checkboxes para ligar/desligar séries; legenda; escala de tempo no eixo X.

Estilo:

CSS leve inspirado no shadcn/ui (tokens de cor, radius, espaçamentos). Observação: shadcn/ui é um conjunto de componentes React/Tailwind; aqui apenas emulamos o look com CSS próprio. 
Shadcn
+1

5) Esquema de dados (CSV)

Cabeçalho padrão (na ordem):
timestamp,gpu_util,memory_util,mem_total_mb,mem_used_mb,temp_c,power_w

Tipos: timestamp ISO-8601 (ou string bruta do nvidia-smi); demais numéricos (float/int).

Observação: o --format=csv do nvidia-smi facilita a coleta tabular; o conjunto de campos é configurável via --query-gpu. 
NVIDIA Docs
+1

6) Requisitos não-funcionais

Plataforma: Windows 10/11; Python 3.10+; driver NVIDIA recente com nvidia-smi. 
NVIDIA Docs

Desempenho: overhead baixo; amostragem padrão 2s. (Permitir 1–10s).

Tolerância a falhas: se o processo cair, o app deve permitir retomar a coleta e continuar append no CSV.

Privacidade/segurança: operação local; a página HTML não faz rede, lê apenas o arquivo selecionado pelo usuário (File API). 
MDN Web Docs

7) Dependências

NVIDIA drivers (incluem nvidia-smi). 
NVIDIA Docs

Chart.js (CDN oficial). 
chartjs.org

8) Critérios de aceite (MVP)

A1: Com intervalo=2s e duracao=60s, o CSV final tem ≈30 linhas (+/-1).

A2: O arquivo CSV abre na página HTML; o gráfico exibe ao menos 2 séries simultâneas.

A3: Alterar o conjunto de colunas no coletor reflete no cabeçalho e a página consegue detectar e listar essas novas colunas.

A4: Botão Parar encerra a coleta em ≤2s; nenhum handle de arquivo fica preso.

A5: Com CSV de 10 mil linhas, a página continua responsiva (zoom/pan do Chart.js fluido). 
chartjs.org

9) Riscos & mitigação

nvidia-smi indisponível (PATH/driver): checagem no start, mensagem com instruções. 
NVIDIA Docs

CSV grande (memória no browser): orientar o usuário a filtrar período (CSV por período) e/ou oferecer opção “amostrar a cada N linhas”.

Diferenças de layout (unidades/locale): normalizar cabeçalho e limpar unidades ao gravar.