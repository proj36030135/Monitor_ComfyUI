# 🚀 Guia de Inicialização - GPU Monitor

Este guia explica como usar os scripts de inicialização para executar o GPU Monitor de forma fácil e automática.

## 📁 Scripts Disponíveis

### 1. `start_app.py` - Script Python Completo ⭐ **Recomendado**
Script Python avançado com recursos completos de monitoramento e controle.

**Características:**
- ✅ Verifica dependências automaticamente
- ✅ Inicia o backend e aguarda ficar disponível
- ✅ Abre automaticamente o navegador
- ✅ Monitora o processo do backend
- ✅ Finalização limpa com Ctrl+C
- ✅ Logs detalhados e coloridos

**Como usar:**
```bash
# Execução simples
python start_app.py

# O script irá:
# 1. Verificar se o backend já está rodando
# 2. Iniciar o servidor backend
# 3. Aguardar o backend ficar disponível
# 4. Abrir automaticamente o navegador
# 5. Manter o backend rodando até você pressionar Ctrl+C
```

### 2. `start_app.bat` - Script Batch para Windows
Script batch simples para usuários Windows que preferem arquivos .bat.

**Características:**
- ✅ Interface simples para Windows
- ✅ Verifica se Python está instalado
- ✅ Inicia backend em segundo plano
- ✅ Abre navegador automaticamente
- ✅ Detecção se backend já está ativo

**Como usar:**
```batch
# Duplo clique no arquivo ou execute no terminal:
start_app.bat
```

### 3. `start_app.ps1` - Script PowerShell Avançado
Script PowerShell com recursos avançados para usuários Windows.

**Características:**
- ✅ Parâmetros personalizáveis
- ✅ Logs coloridos
- ✅ Verificação de saúde do backend
- ✅ Controle fino de timeout
- ✅ Opção de pular abertura do navegador

**Como usar:**
```powershell
# Execução básica
.\start_app.ps1

# Com parâmetros personalizados
.\start_app.ps1 -BackendPort 8080 -WaitTimeout 45 -Verbose

# Apenas iniciar backend (sem abrir navegador)
.\start_app.ps1 -SkipBrowser
```

## 🛠️ Pré-requisitos

### Dependências Python
Certifique-se de que as dependências estão instaladas:

```bash
# No diretório raiz do projeto
pip install requests

# Para o backend (se ainda não instalou)
pip install -r backend/requirements.txt
```

### Estrutura de Diretórios
Os scripts esperam esta estrutura:
```
Monitor ComfyUI/
├── backend/
│   ├── server.py
│   ├── gpu_monitor.py
│   └── requirements.txt
├── viewer/
│   ├── index.html
│   ├── dashboard.js
│   └── styles.css
├── start_app.py      ← Scripts de inicialização
├── start_app.bat     ← 
└── start_app.ps1     ← 
```

## 🚀 Início Rápido

### Opção 1: Script Python (Recomendado)
```bash
python start_app.py
```

### Opção 2: Duplo Clique (Windows)
1. Duplo clique em `start_app.bat`
2. Aguarde o backend inicializar
3. O navegador abrirá automaticamente

### Opção 3: PowerShell (Windows Avançado)
```powershell
.\start_app.ps1
```

## 📊 O Que Acontece Quando Executar

1. **Verificação de Ambiente**
   - ✅ Verifica se Python está disponível
   - ✅ Verifica se as dependências estão instaladas
   - ✅ Verifica estrutura de diretórios

2. **Inicialização do Backend**
   - 🚀 Inicia o servidor FastAPI na porta 8000
   - ⏳ Aguarda o backend ficar disponível
   - 🔍 Verifica saúde do backend via API

3. **Abertura da Interface**
   - 🌐 Abre automaticamente `viewer/index.html` no navegador
   - 🔗 A interface se conecta ao backend automaticamente

4. **Monitoramento**
   - 📊 O dashboard começa a receber dados da GPU imediatamente
   - 🔄 Atualizações em tempo real via WebSocket

## ⚙️ Configurações

### URLs e Portas
- **Backend**: `http://localhost:8000`
- **Frontend**: `file:///caminho/para/viewer/index.html`

### Personalizações
Você pode editar as configurações no início dos scripts:

**start_app.py:**
```python
BACKEND_HOST = "localhost"
BACKEND_PORT = 8000
STARTUP_TIMEOUT = 30  # segundos
```

**start_app.ps1:**
```powershell
.\start_app.ps1 -BackendHost "0.0.0.0" -BackendPort 8080 -WaitTimeout 60
```

## 🔧 Solução de Problemas

### Backend Não Inicia
```bash
# Verifique se as dependências estão instaladas
pip install -r backend/requirements.txt

# Teste manualmente
cd backend
python server.py
```

### Porta Já em Uso
```bash
# Verifique qual processo está usando a porta 8000
netstat -ano | findstr :8000

# Ou use uma porta diferente
.\start_app.ps1 -BackendPort 8080
```

### Navegador Não Abre
- Abra manualmente: `file:///caminho/completo/para/viewer/index.html`
- Ou acesse: `http://localhost:8000` (se o backend tiver interface web)

### Permissões PowerShell
```powershell
# Se houver erro de política de execução
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🎯 Dicas de Uso

### Para Desenvolvimento
```bash
# Use o script Python com logs detalhados
python start_app.py

# Ou use o backend com reload automático
cd backend
python server.py  # já tem reload=True configurado
```

### Para Uso Diário
- Use `start_app.bat` para inicialização rápida
- Crie um atalho na área de trabalho para `start_app.bat`

### Para Automação
```bash
# Script Python pode ser usado em outros scripts
python start_app.py > monitor.log 2>&1 &
```

## 📝 Logs e Monitoramento

### Logs do Script Python
- Logs detalhados com timestamp
- Status de cada etapa da inicialização
- Monitoramento contínuo do backend

### Verificação de Status
Todos os scripts verificam:
- ✅ Se o backend já está rodando
- ✅ Se as dependências estão instaladas
- ✅ Se os arquivos necessários existem
- ✅ Se a porta está disponível

## 🛑 Como Parar

### Script Python
- Pressione `Ctrl+C` no terminal
- O script finalizará o backend automaticamente

### Script Batch
- Feche a janela do terminal
- O backend continuará rodando em segundo plano
- Para parar completamente, finalize o processo Python

### Script PowerShell
- Pressione `Ctrl+C`
- Finalização automática e limpa

---

## 📞 Suporte

Se encontrar problemas:

1. **Verifique os logs** - todos os scripts mostram informações detalhadas
2. **Teste manualmente** - execute o backend diretamente: `cd backend && python server.py`
3. **Verifique dependências** - `pip install -r backend/requirements.txt`
4. **Verifique a estrutura** - certifique-se de que os diretórios `backend/` e `viewer/` existem

**Boa monitoração! 🚀📊**
