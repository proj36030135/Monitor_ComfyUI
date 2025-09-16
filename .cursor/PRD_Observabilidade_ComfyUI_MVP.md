# PRD — Módulo 1: Observabilidade das Gerações de Vídeo (ComfyUI)

**Versão:** 1.0  
**Data:** 2025-09-14  
**Status:** MVP — requisitos funcionais fechados (sem decisões de implementação)

---

## 1) Visão Geral e Objetivo
Dar visibilidade em **tempo quase real** do consumo de recursos durante as gerações no **ComfyUI**, registrando séries temporais por **Sessão** e por **Run**, com possibilidade de consulta histórica e exportação.

---

## 2) Vocabulário (definições funcionais)
- **Sessão**: período contínuo de medição iniciado/pausado/encerrado pelo usuário.
- **Run**: uma execução de geração no ComfyUI (início → fim) dentro de uma sessão.
- **Amostra**: registro pontual das métricas num instante de tempo.
- **Métrica**: dado observado (ex.: utilização da GPU em %).
- **Perfil de hardware**: conjunto nomeado de preferências padrão para medição e visualização.
- **Painel**: tela de visualização das métricas e eventos.

---

## 3) Estados e Regras Gerais
- **Sessão**: `inativa → ativa ↔ pausada → encerrada`  
  - Regra: apenas **1 sessão ativa por instância**.
- **Run**: `pendente → em_execução → {concluído | falhou | cancelado | interrompido}`  
  - Regra: **sem sobreposição** de runs para o mesmo processo; iniciar novo run encerra o anterior como `interrompido`.
- **Tempo e Unidades**: todos os registros usam **UTC ISO‑8601**; a UI pode localizar a exibição. **Timestamps devem ser monotônicos** dentro de uma sessão.
- **Associação Amostras↔Run**: uma amostra pertence a um run se `timestamp ∈ [run_start, run_end]` (bordas inclusivas).

---

## 4) Requisitos Funcionais (RF)

### RF01 — Sessões de medição
**Descrição**: criar, nomear, iniciar, pausar, retomar e encerrar uma sessão. A UI deve exibir claramente o estado atual.  
**Critérios de Aceite**
- Sessão encerrada não aceita novas amostras.
- Mudanças de estado seguem apenas as transições permitidas (acima).
- Apenas 1 sessão ativa por instância.

---

### RF02 — Coleta com intervalo configurável
**Descrição**: o usuário define o **intervalo de amostragem**.  
**Critérios de Aceite**
- Faixa permitida: **0,5s a 10s**; valores fora da faixa são rejeitados com mensagem clara.
- **SLA**: jitter máximo **±20%** do intervalo configurado.
- Alterações de intervalo têm efeito a partir do próximo ciclo de amostragem.

---

### RF03 — Catálogo e seleção de métricas
**Descrição**: o usuário escolhe **quais métricas** coletar/exibir e a **granularidade** (por dispositivo, agregado, por processo).  
**Conjunto mínimo obrigatório**
- **GPU**: `util%`, `mem.used`, `mem.total`, `temp`, `device_index`.
- **CPU**: `util%`.
- **RAM**: `used`, `total`.
- **Processo alvo (ComfyUI)**: `cpu%`, `ram.used`.
**Opcionais (quando disponíveis)**: `gpu.power`, `gpu.encoder.util`, `disk.io`, `fps/kbps do run`.  
**Critérios de Aceite**
- Multi‑GPU: permitir filtro por `device_index`.
- Desmarcar métrica remove sua coleta e sua exibição no painel.

---

### RF04 — Detecção e marcação de *runs*
**Descrição**: registrar eventos `run.start` e `run.end` com `run_id`, `status` e `duração`.  
**Regras**
- Definir **uma fonte canônica de eventos de run** por sessão.
- Sem sobreposição de runs para o mesmo processo; iniciar novo run encerra o anterior como `interrompido`.  
**Critérios de Aceite**
- Em sessões com ≥10 runs, pelo menos **95%** dos runs devem ser detectados e marcados corretamente.
- Amostras entre os marcadores ficam associadas ao `run_id` correspondente.

---

### RF05 — Visualização em tempo quase real
**Descrição**: gráficos de séries temporais atualizados automaticamente com marcadores de eventos.  
**Critérios de Aceite**
- **SLA de UI**: nova amostra refletida na interface em até **2s**.
- **Janelas**: últimos **5/15/60 min** e **toda a sessão**.
- Filtros: por **métrica**, **device_index**, **run_id** e **destaque de um run**.
- Marcadores de `run.start`/`run.end` visíveis na linha do tempo.

---

### RF06 — Consulta de histórico
**Descrição**: listar e abrir sessões passadas, navegar pelos runs e métricas da sessão.  
**Critérios de Aceite**
- Filtros por **nome**, **intervalo de datas**, **perfil** e **tags**.
- **Resumo da sessão**: duração, nº de runs, picos/médias/mín‑máx por métrica.
- Alternar entre visão **por sessão** e **por run**.

---

### RF07 — Anotações e rótulos (tags)
**Descrição**: adicionar/editar **notas** e **tags** em sessão e run.  
**Critérios de Aceite**
- Limites: até **10 tags** por entidade; cada tag até **24** caracteres; nota até **500** caracteres.
- Tags podem ser usadas como **filtro** nas buscas e na listagem de sessões.

---

### RF08 — Perfis de hardware
**Descrição**: cadastrar perfis com nome, descrição e **preferências padrão** (métricas, janela, intervalo). Vincular um perfil ao iniciar sessão aplica suas preferências.  
**Critérios de Aceite**
- Clonar e editar perfil disponíveis.
- Mudanças em perfis não alteram sessões já iniciadas.

---

### RF09 — Parametrização operacional
**Descrição**: definir **preferências globais**: intervalo padrão, métricas padrão, janelas padrão e **limiares visuais** (ex.: aviso quando GPU > X%).  
**Critérios de Aceite**
- Ao alterar preferências, o usuário escolhe se aplica à sessão ativa.
- Limiar no MVP tem efeito **apenas visual** (sem alertas externos).

---

### RF10 — Exportação de dados
**Descrição**: exportar dados para análise externa.  
**Critérios de Aceite**
- **Exportar Sessão** → duas tabelas: **Samples** (todas as amostras da sessão) e **Events** (session.start/end, run.start/end + metadados).
- **Exportar Run** → amostras daquele run + metadados do run.
- Arquivos devem conter **cabeçalho claro**; nomes incluem o **identificador da sessão/run**.

---

### RF11 — Saúde do sistema
**Descrição**: painel de status operacional.  
**Critérios de Aceite**
- Estados: **OK / Degradado / Desconectado**.
  - **Desconectado**: ausência de amostras por **5 intervalos** consecutivos.
  - **Degradado**: latência média de atualização da UI > **2s** por 30s.
- Estado exibido de forma persistente e registrável na sessão.

---

### RF12 — Retenção e rotação
**Descrição**: prevenir crescimento ilimitado de dados por sessão.  
**Critérios de Aceite**
- Limites por sessão: até **1.000.000** amostras **ou** **8 horas** de coleta (o que ocorrer primeiro).
- Ao atingir o limite, o sistema deve **encerrar** a sessão ou **segmentá‑la** (criar sessão encadeada), a critério do usuário.
- A segmentação preserva continuidade temporal e vínculo entre sessões.

---

### RF13 — Acessibilidade, mensagens e estados vazios
**Descrição**: garantir usabilidade mínima e diagnósticos claros.  
**Critérios de Aceite**
- UI com contraste mínimo (WCAG **AA**), tooltip com **unidade/descrição** por métrica e indicador de **taxa de amostragem real**.
- Estados vazios obrigatórios: “sem sessão”, “sem métricas selecionadas”, “sem runs nesta sessão”, cada um com instrução de ação.
- Mensagens de erro devem indicar **o que deu errado** e **como resolver** (frase curta).

---

## 5) Regras de Negócio Complementares
1. **Integridade temporal**: timestamps monotônicos dentro da mesma sessão.
2. **Associatividade**: toda amostra pertence a uma sessão; amostras entre marcadores pertencem ao run correspondente.
3. **Multiplicidade de dispositivos**: métricas dependentes de dispositivo carregam `device_index`; agregados “All GPUs” são derivação explícita.
4. **Validação de intervalo**: intervalo de amostragem não pode ser zero, negativo, ou fora da faixa definida em RF02.
5. **Privacidade**: campos potencialmente sensíveis (ex.: caminhos de arquivo) são opt‑in na exportação.

---

## 6) Métricas de Sucesso do MVP
- ≥ **95%** dos runs detectados em sessões com ≥10 runs.
- **Latência de UI** ≤ **2s** para refletir novas amostras.
- **Perdas de amostra** ≤ **1%** por hora de coleta.
- Capacidade de navegar/filtrar sessões com **≥500k amostras** sem travamentos perceptíveis (pode haver downsample).

---

## 7) Fora de Escopo (MVP)
- Alertas externos (e‑mail, push), dashboards colaborativos, autenticação multiusuário, sobreposição comparativa de múltiplos runs em um mesmo gráfico, integrações com serviços de terceiros.

---

## 8) Anexos — Layouts de Exportação (conceitual)
- **Samples**: `timestamp_iso, session_id, run_id, metric_group, metric_name, value, device_index?`
- **Events**: `timestamp_iso, session_id, event_type (session.start|session.end|run.start|run.end), run_id?, status?, duration_s?, notes?`

> Observação: este PRD define **o que** deve acontecer e os critérios de aceite. Decisões de **como** (bibliotecas, formatos internos, arquitetura) ficam fora deste documento e serão tratadas no ADR/Design Doc.
