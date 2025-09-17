# 🖥️ GPU Monitor Frontend - ShadCN UI

Frontend moderno em Next.js com componentes ShadCN UI para monitoramento de GPU em tempo real.

## ✨ Características

- **🎨 Interface Moderna**: Baseada no design system ShadCN UI
- **📊 Dashboard Interativo**: Métricas em tempo real com gráficos responsivos
- **🔗 Conexão WebSocket**: Streaming de dados em tempo real
- **📱 Responsivo**: Funciona perfeitamente em desktop e mobile
- **🎯 TypeScript**: Tipagem completa para maior segurança
- **🌙 Tema Elegante**: Design limpo e profissional

## 🏗️ Arquitetura

```
frontend/
├── src/
│   ├── app/                  # App Router do Next.js
│   │   ├── page.tsx         # Página principal
│   │   ├── layout.tsx       # Layout global
│   │   └── globals.css      # Estilos globais
│   ├── components/          # Componentes React
│   │   ├── ui/             # Componentes ShadCN UI
│   │   ├── dashboard.tsx   # Dashboard principal
│   │   ├── sidebar.tsx     # Navegação lateral
│   │   ├── gpu-chart.tsx   # Gráfico de métricas
│   │   └── ...
│   ├── hooks/              # Hooks customizados
│   │   └── use-gpu-api.ts  # Hook para API e WebSocket
│   └── lib/
│       └── utils.ts        # Utilitários
└── components.json         # Configuração ShadCN
```

## 🚀 Como Executar

### Pré-requisitos

- Node.js 18+ 
- Backend FastAPI rodando na porta 8000

### Instalação e Execução

```bash
# Instalar dependências
npm install

# Executar em modo de desenvolvimento
npm run dev

# Executar em produção
npm run build
npm start
```

O frontend estará disponível em: http://localhost:3000

## 📊 Funcionalidades do Dashboard

### 🎯 Visão Geral
- **Cards de Métricas**: Utilização média, temperatura máxima, GPUs ativas e potência total
- **Gráfico em Tempo Real**: Visualização de métricas com opções de utilização, temperatura e potência
- **Status das GPUs**: Tabela detalhada com informações de cada GPU
- **Stats em Tempo Real**: Panel lateral com métricas atualizadas constantemente

### 📈 Métricas Disponíveis

- **Utilização**: Percentual de uso da GPU
- **Temperatura**: Temperatura atual em Celsius
- **Memória**: Uso de memória em GB/MB
- **Potência**: Consumo de energia em Watts

### 🔄 Conexão com Backend

- **Auto-reconexão**: Reconecta automaticamente em caso de perda de conexão
- **Status Visual**: Indicadores claros do status da conexão
- **Tratamento de Erros**: Mensagens informativas de erro

## 🎨 Componentes Principais

### Dashboard (`dashboard.tsx`)
- Componente principal que orquestra toda a interface
- Gerencia estado de conexão e dados das GPUs
- Sistema de tabs para diferentes visualizações

### GPUChart (`gpu-chart.tsx`)
- Gráfico em tempo real usando Recharts
- Suporte para diferentes métricas
- Atualização automática a cada 2 segundos

### RealtimeStats (`realtime-stats.tsx`)
- Panel com status atual de cada GPU
- Indicadores visuais de performance
- Barras de progresso animadas

### GPUTable (`gpu-table.tsx`)
- Tabela sorteable com dados detalhados
- Ações contextuais para cada GPU
- Badges de status coloridos

## 🔌 API Integration

### Hook useGPUAPI (`use-gpu-api.ts`)
Hook customizado que gerencia:
- 📡 Conexão WebSocket para dados em tempo real
- 🌐 Requisições HTTP para dados históricos
- 🔄 Auto-reconexão e tratamento de erros
- 📊 Estado centralizado dos dados

### Endpoints Utilizados
- `GET /api/health` - Verificação de saúde do backend
- `GET /api/gpu/current` - Dados atuais das GPUs  
- `GET /api/gpu/stats` - Estatísticas agregadas
- `WS /ws` - Stream de dados em tempo real

## 🎨 Personalização

### Tema e Cores
O projeto usa o sistema de temas do ShadCN UI. Para personalizar:

```typescript
// Em globals.css
:root {
  --primary: 220 87% 56%;
  --secondary: 217 33% 17%;
  /* ... outras variáveis */
}
```

### Adicionando Novos Componentes ShadCN

```bash
npx shadcn@latest add [component-name]
```

### Configuração do Backend
Para alterar a URL do backend, edite em `use-gpu-api.ts`:

```typescript
const [backendUrl, setBackendUrl] = useState('http://localhost:8000')
```

## 🔧 Desenvolvimento

### Estrutura de Commits
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `style:` Mudanças de estilo/UI
- `refactor:` Refatoração de código

### Scripts Disponíveis

```bash
npm run dev        # Servidor de desenvolvimento
npm run build      # Build de produção
npm run start      # Servidor de produção
npm run lint       # Verificar linting
```

## 📱 Responsividade

O dashboard é totalmente responsivo e funciona em:
- 🖥️ Desktop (1920x1080+)
- 💻 Laptop (1366x768+)
- 📱 Tablet (768x1024+)
- 📱 Mobile (375x667+)

### Navegação Mobile
- Sidebar colapsível com Sheet component
- Menu hambúrguer para acesso rápido
- Touch-friendly para interações tácteis

## 🚀 Deploy

### Vercel (Recomendado)
```bash
npm i -g vercel
vercel --prod
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🐛 Troubleshooting

### Backend não conecta
1. Verifique se o backend está rodando na porta 8000
2. Confirme que não há firewall bloqueando a conexão
3. Teste a URL: http://localhost:8000/api/health

### WebSocket falha
1. Verifique se o browser suporta WebSocket
2. Confirme que não há proxy interferindo
3. Observe o console do browser para erros

### Performance lenta
1. Verifique se há muitos dados sendo processados
2. Considere aumentar o intervalo de atualização
3. Use o profiler do React DevTools

## 📞 Suporte

Para problemas específicos do frontend:
1. Verifique o console do navegador (F12)
2. Confirme que todas as dependências estão instaladas
3. Teste com `npm run lint` para verificar erros de código

## 🔮 Roadmap

- [ ] **Temas Customizáveis**: Light/Dark mode toggle
- [ ] **Export de Dados**: CSV, JSON, PDF
- [ ] **Alertas Personalizados**: Notificações de temperatura/uso
- [ ] **Métricas Avançadas**: GPU memory bandwidth, clock speeds
- [ ] **Multi-servidor**: Suporte para múltiplos backends
- [ ] **PWA**: Transformar em Progressive Web App

---

**Feito com ❤️ usando Next.js, ShadCN UI e TypeScript**