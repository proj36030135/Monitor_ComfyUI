# Coletor de GPU (Sprint 1)

## Requisitos
- Windows 10/11
- Python 3.10+
- Driver NVIDIA com `nvidia-smi` no PATH

## Como usar
1. Ative a .venv (PowerShell):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. Execute a UI:
   ```powershell
   python -m collector.app
   ```
3. Configure os parâmetros e clique em Iniciar/Parar.

### Grafico ao vivo
- Instale as dependências (na sua venv): `pip install -r requirements.txt`.
- Com a coleta em execução (ou com um CSV existente em `./logs/gpu_log.csv`), clique em `Abrir Grafico` na UI.
- A janela mostra 4 subplots (GPU, Memória, Temperatura, Potência) e atualiza continuamente.
- Se o arquivo estiver vazio ou ausente, a janela mostra "Aguardando dados" sem erro.
- Fechar a janela interrompe o timer de atualização e libera recursos.

## Saída
- CSV padrão: `./logs/gpu_log.csv`.
- Cabeçalho dinâmico gerado a partir das colunas selecionadas (exemplo):
  ```
  timestamp,gpu_util,memory_util,mem_total_mb,mem_used_mb,temp_c,power_w
  ```

## Logging
- Arquivo: `./logs/collector.log` (rotativo).

## Observações
- Se `nvidia-smi` não estiver disponível, a UI exibirá erro ao iniciar a coleta.
- O backend do Matplotlib usado é TkAgg. Em ambientes sem suporte a Tk, a janela informará o erro e não travará a aplicação.

