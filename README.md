# 🖥️ GPU Monitor

Sistema completo de monitoramento de GPU em tempo real com arquitetura separada frontend/backend.

## 📋 Funcionalidades

- **Backend API**: Coleta dados via nvidia-smi e fornece API REST + WebSocket
- **Frontend Dashboard**: Interface web moderna com gráficos em tempo real
- **Armazenamento**: Banco de dados SQLite para histórico completo
- **Streaming**: WebSocket para dados em tempo real
- **Responsivo**: Interface adaptável para desktop e mobile

## 🔧 Dados Coletados

- `device_index`: Índice da GPU (0, 1, 2, ...)
- `util_percent`: Percentual de utilização da GPU
- `mem_used_mb`: Memória utilizada em MB
- `mem_total_mb`: Memória total em MB
- `temp_celsius`: Temperatura em Celsius
- `power_watts`: Consumo de energia em Watts

## 🏗️ Arquitetura

```
gpu-monitor/
├── backend/                 # API e coleta de dados
│   ├── server.py           # Servidor FastAPI
│   ├── gpu_monitor.py      # Coleta e armazenamento
│   ├── requirements.txt    # Dependências Python
│   ├── test_client.py      # Cliente de teste
│   └── run.py             # Script de execução
├── viewer/                 # Frontend web
│   ├── index.html         # Dashboard principal
│   ├── styles.css         # Estilos
│   ├── dashboard.js       # Lógica JavaScript
│   └── README.md          # Documentação do viewer
└── README.md              # Este arquivo
```

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.8+
- NVIDIA GPU com drivers instalados
- nvidia-smi disponível no PATH
- Navegador web moderno

### 1. Backend - Instalar dependências

```bash
cd backend
pip install -r requirements.txt
```

### 2. Backend - Executar servidor

```bash
cd backend
python run.py
# ou
python server.py
```

O backend estará disponível em: http://localhost:8000

### 3. Frontend - Abrir dashboard

Abra o arquivo `viewer/index.html` diretamente no navegador ou use um servidor HTTP local:

```bash
# Opção 1: Abrir diretamente
# Abra viewer/index.html no navegador

# Opção 2: Servidor HTTP simples (Python)
cd viewer
python -m http.server 3000
# Acesse: http://localhost:3000

# Opção 3: Servidor HTTP simples (Node.js)
cd viewer
npx serve .
```

### 4. Conectar frontend ao backend

1. Abra o dashboard no navegador
2. Verifique se a URL do backend está correta (http://localhost:8000)
3. Clique em "Conectar"
4. Os dados em tempo real aparecerão automaticamente

## 📡 API do Backend

### WebSocket
- `ws://localhost:8000/ws` - Stream de dados em tempo real

### REST Endpoints

#### Informações da API
```http
GET /
```

#### Health Check
```http
GET /api/health
```

#### Dados atuais
```http
GET /api/gpu/current
```

#### Histórico
```http
GET /api/gpu/history?hours=24&device_index=0&limit=1000
```

Parâmetros:
- `hours`: Horas de histórico (1-168)
- `device_index`: GPU específica (opcional)
- `limit`: Limite de registros (1-10000)

#### Estatísticas
```http
GET /api/gpu/stats
```

## 🎨 Frontend Features

### Dashboard Principal
- **Cards de GPU**: Métricas em tempo real para cada GPU
- **Gráficos**: Visualização de utilização, temperatura, memória e potência
- **Status**: Indicadores de conexão e saúde do sistema

### Controles
- **Conexão**: Configurar URL do backend e conectar/desconectar
- **Gráficos**: Pausar/retomar, limpar dados, ajustar período
- **Histórico**: Consultar dados passados com filtros

### Abas
- **Histórico**: Tabela com dados históricos filtráveis
- **Estatísticas**: Resumo estatístico das GPUs
- **Logs**: Log de eventos do sistema com exportação

## 🗃️ Banco de Dados

```sql
CREATE TABLE gpu_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    device_index INTEGER,
    util_percent REAL,
    mem_used_mb REAL,
    mem_total_mb REAL,
    temp_celsius REAL,
    power_watts REAL
);
```

## 📊 Exemplo de Resposta da API

```json
{
  "data": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:45",
      "device_index": 0,
      "util_percent": 85.5,
      "mem_used_mb": 7234.0,
      "mem_total_mb": 8192.0,
      "temp_celsius": 72.0,
      "power_watts": 220.5
    }
  ],
  "count": 1
}
```

## 🔧 Configuração

### Backend - Porta do servidor
Edite `backend/server.py`:
```python
uvicorn.run(
    "server:app",
    host="0.0.0.0",
    port=8080,  # Nova porta
    reload=True
)
```

### Backend - Intervalo de coleta
Edite `backend/server.py`, função `background_monitoring()`:
```python
await asyncio.sleep(5)  # Altere para o intervalo desejado (segundos)
```

### Frontend - URL do backend
No dashboard, altere a URL na interface ou edite `viewer/dashboard.js`:
```javascript
this.backendUrl = 'http://localhost:8000';  // Nova URL
```

## 🐛 Solução de Problemas

### Backend não inicia
```bash
# Verifique se nvidia-smi funciona
nvidia-smi --version

# Verifique dependências
cd backend
pip install -r requirements.txt
```

### Frontend não conecta
1. Verifique se o backend está rodando: http://localhost:8000
2. Verifique CORS no navegador (console F12)
3. Teste a API diretamente: http://localhost:8000/api/health

### Dados não aparecem
1. Verifique se há GPUs NVIDIA no sistema
2. Teste o monitor diretamente: `python backend/gpu_monitor.py`
3. Verifique logs no console do navegador

### WebSocket não conecta
1. Verifique se a URL WebSocket está correta
2. Teste com ferramenta externa (ex: wscat)
3. Verifique firewall/proxy

## 📈 Desenvolvimento

### Executar em modo de desenvolvimento

Backend com auto-reload:
```bash
cd backend
python run.py --reload
```

Frontend com servidor de desenvolvimento:
```bash
cd viewer
python -m http.server 3000
```

### Testar API
```bash
cd backend
python test_client.py
```

### Estrutura de desenvolvimento
- Backend: FastAPI com auto-reload
- Frontend: Vanilla JavaScript (sem build necessário)
- Dados: SQLite (arquivo local)
- Logs: Console + interface web

## 📝 Licença

Este projeto está sob licença MIT.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

Para suporte, abra uma issue no repositório.