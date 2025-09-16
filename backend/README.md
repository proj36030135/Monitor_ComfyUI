# 🔧 GPU Monitor Backend

Backend API para monitoramento de GPU usando FastAPI, WebSocket e SQLite.

## 📋 Funcionalidades

- **Coleta de dados**: nvidia-smi para métricas de GPU
- **API REST**: Endpoints para consulta de dados
- **WebSocket**: Streaming em tempo real
- **SQLite**: Armazenamento persistente
- **CORS**: Configurado para frontend separado

## 🚀 Instalação

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Executar servidor
```bash
# Opção 1: Script facilitador
python run.py

# Opção 2: Diretamente
python server.py

# Opção 3: Com uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 Endpoints

### Informações
- `GET /` - Informações da API

### Health Check
- `GET /api/health` - Status do sistema

### Dados de GPU
- `GET /api/gpu/current` - Dados mais recentes
- `GET /api/gpu/history` - Histórico com filtros
- `GET /api/gpu/stats` - Estatísticas resumidas

### WebSocket
- `WS /ws` - Stream de dados em tempo real

## 🔧 Configuração

### Variáveis de ambiente
```bash
# Porta do servidor (padrão: 8000)
export PORT=8000

# Host (padrão: 0.0.0.0)
export HOST=0.0.0.0

# Intervalo de coleta em segundos (padrão: 2)
export COLLECTION_INTERVAL=2
```

### Arquivo de configuração
Edite `server.py` para alterar configurações:

```python
# Porta
uvicorn.run("server:app", port=8080)

# Intervalo de coleta
await asyncio.sleep(5)  # 5 segundos
```

## 🗄️ Banco de Dados

O banco SQLite é criado automaticamente em `gpu_monitor.db`.

### Schema
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

### Índices
```sql
CREATE INDEX idx_timestamp ON gpu_data(timestamp);
CREATE INDEX idx_device_timestamp ON gpu_data(device_index, timestamp);
```

## 📊 Exemplos de Uso

### Teste básico
```bash
python gpu_monitor.py
```

### Cliente de teste
```bash
python test_client.py
```

### Consulta direta da API
```bash
# Health check
curl http://localhost:8000/api/health

# Dados atuais
curl http://localhost:8000/api/gpu/current

# Histórico (última hora)
curl "http://localhost:8000/api/gpu/history?hours=1"

# Estatísticas
curl http://localhost:8000/api/gpu/stats
```

### WebSocket (usando wscat)
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws
```

## 🔍 Monitoramento

### Logs
O servidor registra logs no console com níveis:
- INFO: Operações normais
- WARNING: Situações de atenção
- ERROR: Erros que precisam de correção

### Métricas
- Conexões WebSocket ativas
- Número de GPUs detectadas
- Status do banco de dados
- Última coleta de dados

## 🐛 Troubleshooting

### nvidia-smi não encontrado
```bash
# Verificar se está no PATH
which nvidia-smi
nvidia-smi --version

# Adicionar ao PATH se necessário
export PATH=$PATH:/usr/bin
```

### Erro de permissão no banco
```bash
# Verificar permissões do diretório
ls -la gpu_monitor.db
chmod 644 gpu_monitor.db
```

### Porta em uso
```bash
# Verificar processos na porta
lsof -i :8000
netstat -tlnp | grep :8000

# Usar porta diferente
python run.py --port 8080
```

### Dependências não instaladas
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt

# Verificar versões
pip list | grep -E "(fastapi|uvicorn|websockets)"
```

## 📈 Performance

### Otimizações implementadas
- Índices no banco de dados
- Conexões SQLite reutilizadas
- WebSocket com broadcast eficiente
- Coleta assíncrona em background

### Monitoramento de performance
- Use `htop` para CPU/memória
- Use `iotop` para I/O de disco
- Monitore logs para erros

### Limites recomendados
- Máximo 100 conexões WebSocket simultâneas
- Coleta mínima a cada 1 segundo
- Retenção de dados: configurável (padrão: ilimitado)

## 🔐 Segurança

### CORS
Configurado para aceitar qualquer origem em desenvolvimento:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Altere em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Produção
Para produção, configure:
1. Origins específicas no CORS
2. HTTPS/WSS
3. Autenticação se necessário
4. Rate limiting
5. Proxy reverso (nginx/Apache)

## 📦 Deploy

### Docker (exemplo)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "server.py"]
```

### Systemd (Linux)
```ini
[Unit]
Description=GPU Monitor Backend
After=network.target

[Service]
Type=simple
User=gpu-monitor
WorkingDirectory=/opt/gpu-monitor/backend
ExecStart=/usr/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🧪 Testes

### Teste unitário
```bash
# Instalar pytest
pip install pytest pytest-asyncio httpx

# Executar testes (quando implementados)
pytest tests/
```

### Teste de carga
```bash
# Usar wrk ou similar
wrk -t12 -c400 -d30s http://localhost:8000/api/health
```

## 📝 Logs

### Localização
Logs são exibidos no console. Para persistir:

```bash
# Redirecionar para arquivo
python server.py > gpu-monitor.log 2>&1

# Usar com systemd
journalctl -u gpu-monitor -f
```

### Níveis de log
Altere em `server.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # Mais verboso
```
