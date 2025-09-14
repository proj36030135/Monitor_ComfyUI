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
