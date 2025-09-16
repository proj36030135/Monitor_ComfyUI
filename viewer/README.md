# 🎨 GPU Monitor Frontend

Dashboard web moderno para visualização de dados de GPU em tempo real.

## 📋 Funcionalidades

- **Dashboard em tempo real**: Cards com métricas de cada GPU
- **Gráficos interativos**: Chart.js com zoom e pan
- **Histórico**: Consulta de dados passados com filtros
- **Estatísticas**: Resumo estatístico das GPUs
- **Logs**: Sistema de logging com exportação
- **Responsivo**: Funciona em desktop e mobile

## 🚀 Como usar

### Opção 1: Abrir diretamente no navegador
```bash
# Simplesmente abra o arquivo no navegador
open viewer/index.html
# ou
start viewer/index.html  # Windows
```

### Opção 2: Servidor HTTP local (recomendado)
```bash
# Python
cd viewer
python -m http.server 3000
# Acesse: http://localhost:3000

# Node.js
cd viewer
npx serve .
# ou
npm install -g live-server
live-server
```

### Opção 3: Servidor web (Apache/Nginx)
Configure o servidor para servir os arquivos estáticos da pasta `viewer/`.

## 🔧 Configuração

### 1. Backend URL
No dashboard, configure a URL do backend:
- Padrão: `http://localhost:8000`
- Para outro host: `http://192.168.1.100:8000`
- Para HTTPS: `https://seu-dominio.com`

### 2. Configuração no código
Edite `dashboard.js` se necessário:
```javascript
class GPUDashboard {
    constructor() {
        this.backendUrl = 'http://localhost:8000';  // Altere aqui
        this.updateInterval = 2000;  // Intervalo de atualização
        this.maxDataPoints = 100;    // Pontos máximos no gráfico
    }
}
```

## 📊 Interface

### Header
- **Status do Backend**: Indica conexão com a API
- **Status WebSocket**: Indica streaming em tempo real
- **Contador de GPUs**: Número de GPUs detectadas

### Controles
- **URL do Backend**: Campo editável para configurar endpoint
- **Intervalo**: Configuração de atualização (não implementado)
- **Conectar/Desconectar**: Controle de conexão
- **Limpar Dados**: Remove dados dos gráficos

### Cards de GPU
Cada GPU tem um card com:
- **Status**: Ativa/Inativa baseado na utilização
- **Utilização**: Percentual com barra visual
- **Temperatura**: Graus Celsius com indicador de alerta
- **Memória**: Uso/total com percentual
- **Potência**: Watts consumidos

### Gráficos
Quatro gráficos em tempo real:
- **Utilização (%)**: 0-100%
- **Temperatura (°C)**: Temperatura em Celsius
- **Memória (MB)**: Uso de memória em MB
- **Potência (W)**: Consumo em Watts

Controles dos gráficos:
- **Período**: 5min, 15min, 30min, 1h
- **Pausar/Retomar**: Pausa atualização dos gráficos
- **Zoom**: Disponível nos gráficos (mouse wheel)

### Abas

#### Histórico
- **Período**: Última hora, 6h, 24h, semana
- **GPU**: Filtrar por GPU específica ou todas
- **Tabela**: Dados históricos paginados

#### Estatísticas
- **Resumo**: Período e total de amostras
- **Cards por GPU**: Médias, mínimos e máximos
- **Métricas**: Utilização, temperatura, potência, memória

#### Logs
- **Eventos**: Log de conexões, erros, etc.
- **Exportar**: Salvar logs como arquivo .txt
- **Limpar**: Remove todos os logs

## 🎨 Personalização

### Cores
Edite `styles.css` para alterar o tema:
```css
:root {
  --bg-primary: #0b0f14;      /* Fundo principal */
  --accent-primary: #2f81f7;   /* Cor de destaque */
  --success: #3ddc97;          /* Verde (conectado) */
  --error: #ff6b6b;            /* Vermelho (erro) */
}
```

### Layout
- **Grid de GPUs**: Ajusta automaticamente baseado no espaço
- **Gráficos**: Grid responsivo 2x2 em desktop, 1x4 em mobile
- **Breakpoints**: 768px para mobile

### Gráficos
Personalizar Chart.js em `dashboard.js`:
```javascript
const chartOptions = {
    // Opções do Chart.js
    scales: {
        y: {
            beginAtZero: true,
            max: 100  // Máximo do eixo Y
        }
    }
};
```

## 🔌 Integração com Backend

### Conexão inicial
1. Frontend testa `/api/health`
2. Se OK, conecta WebSocket em `/ws`
3. Recebe dados iniciais
4. Inicia recebimento em tempo real

### Mensagens WebSocket
```javascript
// Dados em tempo real
{
    "type": "gpu_data",
    "timestamp": "2024-01-15T10:30:45",
    "data": [...]
}

// Dados iniciais
{
    "type": "initial_data",
    "timestamp": "2024-01-15T10:30:45",
    "data": [...]
}

// Resposta a ping
{
    "type": "pong",
    "timestamp": "2024-01-15T10:30:45"
}
```

### APIs REST utilizadas
- `GET /api/health` - Status do sistema
- `GET /api/gpu/current` - Dados mais recentes
- `GET /api/gpu/history` - Histórico com filtros
- `GET /api/gpu/stats` - Estatísticas resumidas

## 📱 Responsividade

### Desktop (>768px)
- Header horizontal com status
- Grid 2-3 colunas para GPUs
- Gráficos em grid 2x2
- Controles inline

### Mobile (≤768px)
- Header vertical empilhado
- GPUs em coluna única
- Gráficos empilhados
- Controles em coluna

### Tablets
- Layout híbrido baseado no espaço disponível
- Gráficos adaptam automaticamente

## 🐛 Troubleshooting

### Dashboard não carrega
1. Verifique se os arquivos estão acessíveis
2. Abra Developer Tools (F12) para ver erros
3. Teste em servidor HTTP local

### Não conecta ao backend
1. Verifique se backend está rodando: http://localhost:8000
2. Teste URL diretamente no navegador
3. Verifique CORS no console (F12)
4. Confirme URL no campo de configuração

### Gráficos não aparecem
1. Verifique se Chart.js carregou (console F12)
2. Teste se dados estão chegando (aba Network)
3. Verifique se WebSocket está conectado

### Performance lenta
1. Reduza `maxDataPoints` em `dashboard.js`
2. Pause gráficos se não necessários
3. Feche outras abas do navegador
4. Use navegador moderno (Chrome, Firefox, Edge)

## 🔧 Desenvolvimento

### Estrutura dos arquivos
```
viewer/
├── index.html      # HTML principal
├── styles.css      # Estilos CSS
├── dashboard.js    # Lógica JavaScript
└── README.md       # Esta documentação
```

### Dependências externas (CDN)
- Chart.js v4.4.3 - Gráficos
- date-fns adapter - Escalas de tempo
- chartjs-plugin-zoom - Zoom nos gráficos

### Desenvolvimento local
```bash
# Servidor com auto-reload
cd viewer
python -m http.server 3000

# Ou com Node.js
npx live-server
```

### Debug
1. Abra Developer Tools (F12)
2. Console: Veja logs e erros
3. Network: Monitore requisições
4. WebSocket: Veja mensagens em tempo real

## 🚀 Deploy

### Servidor web estático
```nginx
server {
    listen 80;
    server_name gpu-monitor.exemplo.com;
    
    location / {
        root /var/www/gpu-monitor/viewer;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### CDN/Hospedagem estática
- GitHub Pages
- Netlify
- Vercel
- AWS S3 + CloudFront

### Docker
```dockerfile
FROM nginx:alpine
COPY viewer/ /usr/share/nginx/html/
EXPOSE 80
```

## 📊 Métricas e Analytics

### Performance
- Tempo de carregamento inicial
- FPS dos gráficos
- Uso de memória do navegador

### Uso
- Conexões simultâneas
- Tempo de sessão
- Funcionalidades mais utilizadas

### Monitoramento
- Erros JavaScript
- Falhas de conexão
- Latência das requisições

## 🔐 Segurança

### Considerações
- Dados não sensíveis (métricas de GPU)
- Conexão via HTTPS recomendada em produção
- CORS configurado no backend

### Boas práticas
- Use HTTPS para WebSocket (WSS)
- Valide dados recebidos do backend
- Sanitize inputs do usuário
- Implemente rate limiting se necessário