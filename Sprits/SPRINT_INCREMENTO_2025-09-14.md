# Sprint de Incremento — 2025-09-14 a 2025-09-20

## Objetivo
Implementar um módulo de gráficos ao vivo (livestream) integrado à interface do coletor (Tkinter), usando Matplotlib com backend TkAgg, para visualizar métricas da GPU registradas em `logs/gpu_log.csv` sem travar a UI.

## Escopo e Entregáveis
- Janela de gráfico ao vivo em Tkinter com `FigureCanvasTkAgg`.
- Leitura incremental do CSV (tail) com atualização contínua.
- Visualizações das colunas: `gpu_util`, `memory_util`, `temp_c`, `power_w` (eixo X: `timestamp`).
- Botão na UI do coletor para abrir/fechar a janela de gráficos.
- Atualização eficiente (blitting quando estável; fallback para redraw completo).
- Encerramento limpo ao fechar a janela (cancelar timers, liberar recursos).
- `requirements.txt` contendo `matplotlib` e revisão de documentação.

## Critérios de Aceite
- Abrir a janela de gráficos sem travamentos, mesmo com coleta ativa.
- Latência de atualização máxima percebida: ≤ 1s (taxa padrão ~2 Hz).
- Com arquivo inexistente ou vazio, a janela exibe estado “Aguardando dados” sem erro.
- Fechamento da janela cancela a atualização e não deixa threads/timers pendentes.
- Sem regressões na coleta, sem erros no log e sem alertas do linter.

## Plano Técnico
- Backend: `matplotlib` com `TkAgg`.
- Componente: classe `LiveChartWindow` (Tkinter `Toplevel`).
  - Cria `Figure`, eixos (2x2 subplots: Utilização GPU, Utilização Memória, Temperatura, Potência).
  - Linhas animadas com `animated=true`; uso de `copy_from_bbox`/`blit` quando estáveis.
  - Fallback automático para `canvas.draw_idle()` se o blit não estiver disponível/estável.
- Leitura incremental do CSV:
  - Abrir arquivo em modo leitura; manter `file_offset` e verificar tamanho para detectar truncamento/sobrescrita.
  - Reprocessar `header` ao detectar reinício do arquivo e remapear colunas.
  - Ignorar linhas parcialmente escritas; processar apenas linhas completas.
  - Buffer circular limitado (ex.: últimas 5.000 amostras).
- Scheduler de atualização:
  - Usar `Tk.after(interval_ms, callback)` (ex.: 500 ms configurável).
  - Desacoplar leitura e renderização.
- Encerramento:
  - `protocol("WM_DELETE_WINDOW", on_close)` para cancelar o `after`, fechar arquivo e limpar `Figure`/`Canvas`.
- Integração com a UI existente:
  - Botão “Abrir Gráfico” na janela principal (`App`) que instancia `LiveChartWindow` (apenas uma por vez).
  - Se já existir, focar a janela aberta.

## Riscos e Mitigações
- Backend TkAgg indisponível: validar e exibir mensagem clara; fallback sem blit.
- CSV muito grande: leitura incremental e buffer circular.
- CSV rotacionado/overwrite: detectar e reinicializar leitura.
- Blitting instável em alguns ambientes: fallback para redraw completo.

## Cronograma (1 semana)
- Dia 1 (Dom 14/09): Estrutura `LiveChartWindow`, canvas e layout; botão placeholder.
- Dia 2 (Seg 15/09): Leitura incremental do CSV e atualização básica sem blit.
- Dia 3 (Ter 16/09): Otimizações e blitting; taxa de atualização configurável.
- Dia 4 (Qua 17/09): Tratamento de erros/edge cases; fechamento limpo; testes manuais.
- Dia 5 (Qui 18/09): Integração final na UI; testes com `nvidia-smi` em execução.
- Dia 6 (Sex 19/09): Documentação, `requirements.txt`, revisão de logs e linter.
- Dia 7 (Sáb 20/09): Correções finais e preparação de release.

## Itens de Trabalho
1. Implementar `LiveChartWindow` com Matplotlib/TkAgg e layout 2x2.
2. Implementar leitor incremental do CSV com detecção de truncamento e buffer circular.
3. Atualização periódica via `Tk.after` e blitting com fallback.
4. Integrar botão “Abrir Gráfico” na UI principal e gestão de janela única.
5. Criar `requirements.txt` (incluir `matplotlib>=3.8,<3.10`).
6. Atualizar documentação (README do coletor e guia rápido de uso).
7. Testes manuais em Windows e revisão de logs/performance.

## Dependências
- Python 3.x compatível com Tkinter.
- `matplotlib` instalado; backend TkAgg disponível.
- `nvidia-smi` gerando `logs/gpu_log.csv` (ou arquivo de exemplo para testes).

## Definition of Done (DoD)
- Critérios de aceite atendidos.
- Sem erros de linter.
- Documentação atualizada, incluindo instruções de uso do gráfico.
- Execução verificada no Windows.

## Métricas de Sucesso
- FPS médio do gráfico ≥ 2 Hz com CPU adicional ≤ 10%.
- Tempo de abertura da janela ≤ 1s.
- Zero exceções não tratadas em 15 min de uso.

## Comunicação
- Status diário curto no repositório (comentários no PR ou log da sprint).
- Issues vinculadas aos commits para rastreabilidade.

## Checklist de Release
- [ ] Janela de gráficos funcional e integrada.
- [ ] Botão na UI principal.
- [ ] `requirements.txt` criado/atualizado.
- [ ] Documentação revisada.
- [ ] Testes manuais concluídos sem erros.
