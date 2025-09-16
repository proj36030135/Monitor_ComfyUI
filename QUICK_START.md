# 🚀 GPU Monitor - Início Rápido

## ⚡ Setup Rápido (2 minutos)

### 1. Backend - Instalar e executar
```bash
cd backend
pip install -r requirements.txt
python run.py
```
✅ Backend rodando em: http://localhost:8000

### 2. Frontend - Abrir dashboard
```bash
# Opção A: Abrir diretamente
open viewer/index.html

# Opção B: Servidor local (recomendado)
cd viewer
python -m http.server 3000
# Acesse: http://localhost:3000
```

### 3. Conectar
1. Abra o dashboard no navegador
2. Clique em "Conectar"
3. Veja os dados em tempo real! 🎉

## 🎯 Comandos Úteis

### Backend
```bash
cd backend

# Executar servidor
python run.py
# ou
python server.py

# Testar coleta de dados
python gpu_monitor.py

# Testar API
python test_client.py

# Servidor em porta diferente
python run.py --port 8080
```

### Frontend
```bash
cd viewer

# Servidor Python
python -m http.server 3000

# Servidor Node.js
npx serve .
# ou
npx live-server
```

## 📊 URLs Principais

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000 (se usando servidor)
- **Health Check**: http://localhost:8000/api/health
- **Dados atuais**: http://localhost:8000/api/gpu/current

## 🔧 Configurações Rápidas

### Alterar porta do backend
Edite `backend/server.py`:
```python
uvicorn.run("server:app", port=8080)  # Nova porta
```

### Alterar URL no frontend
No dashboard, altere o campo "URL do Backend" ou edite `viewer/dashboard.js`:
```javascript
this.backendUrl = 'http://localhost:8080';
```

### Alterar intervalo de coleta
Edite `backend/server.py`:
```python
await asyncio.sleep(5)  # 5 segundos entre coletas
```

## ✅ Checklist de Verificação

### ✅ Backend funcionando
- [ ] `nvidia-smi --version` funciona
- [ ] `python backend/gpu_monitor.py` mostra dados
- [ ] http://localhost:8000/api/health retorna OK
- [ ] Arquivo `gpu_monitor.db` foi criado

### ✅ Frontend funcionando
- [ ] Dashboard abre no navegador
- [ ] Status mostra "Backend: Conectado"
- [ ] Status mostra "WebSocket: Conectado"
- [ ] Cards de GPU aparecem
- [ ] Gráficos mostram dados

## 🐛 Problemas Comuns

### nvidia-smi não encontrado
```bash
# Verificar se está instalado
nvidia-smi --version

# Se não, instalar drivers NVIDIA
```

### Backend não conecta
```bash
# Verificar se porta está livre
netstat -tlnp | grep :8000

# Tentar porta diferente
python backend/run.py --port 8080
```

### Frontend não conecta ao backend
1. Verifique se backend está rodando: http://localhost:8000
2. Verifique URL no campo de configuração
3. Abra console do navegador (F12) para ver erros

### Sem dados de GPU
```bash
# Testar coleta diretamente
python backend/gpu_monitor.py

# Verificar se há GPUs NVIDIA
nvidia-smi
```

## 📱 Acesso Remoto

### Backend em rede local
```bash
# Backend aceita conexões externas por padrão
python backend/run.py --host 0.0.0.0
```

### Frontend aponta para IP remoto
No dashboard, altere URL para:
```
http://192.168.1.100:8000
```

## 🔄 Atualizações

### Atualizar dependências
```bash
cd backend
pip install --upgrade -r requirements.txt
```

### Backup dos dados
```bash
# Copiar banco de dados
cp backend/gpu_monitor.db backup/
```

## 📈 Próximos Passos

1. **Explorar o dashboard**: Veja todas as abas e funcionalidades
2. **Configurar alertas**: Monitore temperaturas altas
3. **Histórico**: Analise tendências de uso
4. **API**: Integre com outros sistemas
5. **Deploy**: Configure para produção

## 🆘 Ajuda Rápida

### Logs do backend
```bash
# Ver logs em tempo real
cd backend
python server.py

# Salvar logs em arquivo
python server.py > gpu-monitor.log 2>&1
```

### Reset completo
```bash
# Parar tudo
# Ctrl+C no backend

# Limpar dados
rm backend/gpu_monitor.db

# Reiniciar
python backend/run.py
```

### Teste rápido da API
```bash
# Health check
curl http://localhost:8000/api/health

# Dados atuais
curl http://localhost:8000/api/gpu/current

# WebSocket (com wscat)
npm install -g wscat
wscat -c ws://localhost:8000/ws
```

Pronto! Seu sistema está funcionando! 🎉

Para mais detalhes, veja o [README.md](README.md) completo.