# Documentação — Monitor ComfyUI

## Instalação e Execução

### 1) Ambiente Python (.venv)
- Windows PowerShell:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

### 2) Coletor (Sprint 1)
```powershell
python -m collector.app
```
- Configure intervalo (s), duração (s), GPU index (opcional), colunas e CSV path.
- Iniciar/Parar conforme necessário. Logs em `./logs/collector.log`.

### 3) Viewer (Sprint 2 e 3)
- Abra `viewer/index.html` no navegador.
- Selecione o CSV gerado.
- Use checkboxes para alternar séries.
- Em “Amostras (decimação)”, ajuste a quantidade de pontos para performance.
- Habilite "Zoom/Pan" para navegação. Use "Resetar zoom" para voltar.

## Testes de Aceite (A1–A5)
- A1: Execução 60s com intervalo 2s → ~30 linhas no CSV (ver `logs/gpu_log.csv`).
- A2: Abrir CSV no viewer e exibir ≥2 séries simultaneamente.
- A3: Alterar `colunas_query` no coletor (ex.: adicionar `clocks.gr`) → cabeçalho muda e viewer lista a coluna nova.
- A4: Botão Parar encerra a coleta em ≤2s e libera o arquivo.
- A5: CSV com 10k linhas permanece fluido com decimação ativa; zoom/pan opcionais funcionam.

## Dicas de Performance
- Use decimação LTTB com amostras entre 800–2000 para arquivos grandes.
- Desative zoom/pan se não estiver usando.
- Prefira fatiar períodos longos em arquivos separados no coletor.

## Problemas Comuns
- `nvidia-smi` não encontrado: instale/atualize drivers e garanta o PATH.
- CSV com colunas não numéricas: o viewer ignora automaticamente em séries.
- Locale com vírgula decimal: o coletor usa `nounits`, valores são numéricos simples.
