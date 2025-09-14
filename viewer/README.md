# Viewer de CSV do GPU Monitor (Sprint 2)

## Uso
- Abra `viewer/index.html` diretamente no navegador (sem servidor).
- Clique em “Arquivo CSV” e selecione um CSV gerado pelo coletor.
- Marque/desmarque colunas para exibir séries no gráfico.

## Recursos
- Chart.js `timeseries` no eixo X, com decimação LTTB habilitada.
- Detecção automática de colunas numéricas.
- UI leve (dark) com checkboxes de séries e legenda.

## Observações
- Timestamp deve estar na primeira coluna com nome `timestamp` (padrão do coletor).
- Colunas numéricas típicas: `gpu_util`, `memory_util`, `mem_used_mb`, `temp_c`, `power_w`.
