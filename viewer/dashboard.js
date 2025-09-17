/**
 * Dashboard JavaScript para GPU Monitor
 * Conecta ao backend via WebSocket e API REST
 */

class GPUDashboard {
    constructor() {
        this.backendUrl = 'http://localhost:8000';
        this.wsUrl = 'ws://localhost:8000/ws';
        this.websocket = null;
        this.isConnected = false;
        this.updateInterval = 2000;
        this.mainChart = null;
        this.chartData = {};
        this.maxDataPoints = 100;
        this.chartsPaused = false;
        this.chartConfig = {
            selectedMetrics: ['utilization'],
            selectedGPUs: [],
            yAxisMode: 'auto',
            yAxisMin: 0,
            yAxisMax: 100
        };
        this.presets = JSON.parse(localStorage.getItem('chart-presets') || '{}');
        this.logs = [];
        this.currentSession = null;
        this.sessions = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.updateBackendUrl();
    }
    
    setupEventListeners() {
        // Controles de conexão
        document.getElementById('connect-btn').addEventListener('click', () => this.connect());
        document.getElementById('disconnect-btn').addEventListener('click', () => this.disconnect());
        document.getElementById('backend-url').addEventListener('change', (e) => {
            this.updateBackendUrl();
        });
        
        // Controles de gráficos
        document.getElementById('pause-charts').addEventListener('click', () => this.toggleCharts());
        document.getElementById('clear-data-btn').addEventListener('click', () => this.clearChartData());
        
        // Controles do gráfico dinâmico
        document.querySelectorAll('input[name="metric"]').forEach(input => {
            input.addEventListener('change', () => this.updateChartConfig());
        });
        
        document.querySelectorAll('input[name="y-axis-mode"]').forEach(input => {
            input.addEventListener('change', () => this.toggleYAxisMode());
        });
        
        document.getElementById('y-axis-min').addEventListener('input', () => this.updateYAxisRange());
        document.getElementById('y-axis-max').addEventListener('input', () => this.updateYAxisRange());
        
        // Controles de presets
        document.getElementById('save-preset').addEventListener('click', () => this.savePreset());
        document.getElementById('load-preset').addEventListener('click', () => this.loadPreset());
        document.getElementById('delete-preset').addEventListener('click', () => this.deletePreset());
        document.getElementById('preset-selector').addEventListener('change', () => this.onPresetSelect());
        
        // Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Histórico
        document.getElementById('load-history').addEventListener('click', () => this.loadHistory());
        
        // Logs
        document.getElementById('clear-logs').addEventListener('click', () => this.clearLogs());
        document.getElementById('export-logs').addEventListener('click', () => this.exportLogs());
        
        // Controles de Sessão
        document.getElementById('session-name').addEventListener('input', () => this.updateSessionButtons());
        document.getElementById('create-session-btn').addEventListener('click', () => this.createSession());
        document.getElementById('start-session-btn').addEventListener('click', () => this.startSession());
        document.getElementById('stop-session-btn').addEventListener('click', () => this.stopSession());
        
        // Gerenciamento de Sessões
        document.getElementById('refresh-sessions').addEventListener('click', () => this.loadSessions());
        document.getElementById('sessions-filter').addEventListener('change', () => this.filterSessions());
    }
    
    updateBackendUrl() {
        const urlInput = document.getElementById('backend-url');
        this.backendUrl = urlInput.value.trim();
        this.wsUrl = this.backendUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
    }
    
    async connect() {
        try {
            this.log('Conectando ao backend...', 'info');
            
            // Testa conexão com API REST primeiro
            const response = await fetch(`${this.backendUrl}/api/health`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const healthData = await response.json();
            this.updateStatus('backend-status', 'connected', 'Conectado');
            this.updateGPUCount(healthData.gpu_count);
            this.log(`Backend conectado: ${healthData.gpu_count} GPU(s) detectada(s)`, 'success');
            
            // Conecta WebSocket
            await this.connectWebSocket();
            
            // Atualiza controles
            document.getElementById('connect-btn').disabled = true;
            document.getElementById('disconnect-btn').disabled = false;
            
            // Carrega dados iniciais
            await this.loadStats();
            this.populateHistoryGPUSelect();
            await this.loadCurrentSession();
            await this.loadSessions();
            this.updateSessionButtons();
            
            // Atualiza seletor de GPUs para gráfico
            setTimeout(() => this.updateGPUSelector(), 1000);
            
        } catch (error) {
            this.log(`Erro ao conectar: ${error.message}`, 'error');
            this.updateStatus('backend-status', 'disconnected', 'Erro');
        }
    }
    
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                this.websocket = new WebSocket(this.wsUrl);
                
                this.websocket.onopen = () => {
                    this.isConnected = true;
                    this.updateStatus('ws-status', 'connected', 'Conectado');
                    this.log('WebSocket conectado', 'success');
                    resolve();
                };
                
                this.websocket.onmessage = (event) => {
                    this.handleWebSocketMessage(event.data);
                };
                
                this.websocket.onclose = (event) => {
                    this.isConnected = false;
                    this.updateStatus('ws-status', 'disconnected', 'Desconectado');
                    this.log(`WebSocket desconectado: ${event.code}`, 'warning');
                };
                
                this.websocket.onerror = (error) => {
                    this.log('Erro WebSocket', 'error');
                    reject(error);
                };
                
                // Timeout para conexão
                setTimeout(() => {
                    if (!this.isConnected) {
                        reject(new Error('Timeout na conexão WebSocket'));
                    }
                }, 5000);
                
            } catch (error) {
                reject(error);
            }
        });
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        this.isConnected = false;
        this.updateStatus('backend-status', 'disconnected', 'Desconectado');
        this.updateStatus('ws-status', 'disconnected', 'Desconectado');
        
        document.getElementById('connect-btn').disabled = false;
        document.getElementById('disconnect-btn').disabled = true;
        
        this.log('Desconectado do backend', 'info');
    }
    
    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'gpu_data':
                    this.updateGPUCards(message.data);
                    this.updateCharts(message.data);
                    break;
                    
                case 'initial_data':
                    this.log('Dados iniciais recebidos', 'info');
                    if (message.data && message.data.length > 0) {
                        this.updateGPUCards([message.data[0]]);
                    }
                    break;
                    
                case 'pong':
                    // Resposta ao ping - mantém conexão viva
                    break;
                    
                case 'session_started':
                    this.log(`Sessão ${message.session_id} iniciada`, 'success');
                    this.loadCurrentSession();
                    this.loadSessions();
                    this.updateSessionButtons();
                    break;
                    
                case 'session_stopped':
                    this.log(`Sessão ${message.session_id} finalizada`, 'info');
                    this.loadCurrentSession();
                    this.loadSessions();
                    this.updateSessionButtons();
                    break;
                    
                default:
                    console.log('Mensagem WebSocket desconhecida:', message);
            }
            
        } catch (error) {
            this.log(`Erro ao processar mensagem: ${error.message}`, 'error');
        }
    }
    
    updateStatus(elementId, status, text) {
        const element = document.getElementById(elementId);
        element.className = `status-value ${status}`;
        element.textContent = text;
    }
    
    updateGPUCount(count) {
        document.getElementById('gpu-count').textContent = count;
    }
    
    updateGPUCards(gpuDataList) {
        const container = document.getElementById('gpu-cards');
        
        gpuDataList.forEach(gpu => {
            const gpuId = `gpu-card-${gpu.device_index}`;
            let card = document.getElementById(gpuId);
            
            if (!card) {
                // Cria novo card se não existir
                card = this.createGPUCard(gpu);
                card.id = gpuId;
                container.appendChild(card);
            } else {
                // Atualiza card existente
                this.updateGPUCardContent(card, gpu);
            }
        });
    }
    
    createGPUCard(gpu) {
        const card = document.createElement('div');
        card.className = 'gpu-card slide-in';
        
        const memoryPercent = (gpu.mem_used_mb / gpu.mem_total_mb * 100).toFixed(1);
        const isHighTemp = gpu.temp_celsius > 80;
        const isHighUtil = gpu.util_percent > 90;
        
        card.innerHTML = `
            <div class="gpu-card-header">
                <h3 class="gpu-title">GPU ${gpu.device_index}</h3>
                <span class="gpu-status ${gpu.util_percent > 0 ? 'active' : 'inactive'}">
                    ${gpu.util_percent > 0 ? 'Ativa' : 'Inativa'}
                </span>
            </div>
            <div class="gpu-metrics">
                <div class="metric">
                    <span class="metric-label">Utilização</span>
                    <span class="metric-value">${gpu.util_percent}%</span>
                    <div class="metric-bar">
                        <div class="metric-bar-fill ${isHighUtil ? 'critical' : ''}" 
                             style="width: ${gpu.util_percent}%"></div>
                    </div>
                </div>
                <div class="metric">
                    <span class="metric-label">Temperatura</span>
                    <span class="metric-value">${gpu.temp_celsius}°C</span>
                    <div class="metric-bar">
                        <div class="metric-bar-fill ${isHighTemp ? 'critical' : ''}" 
                             style="width: ${Math.min(gpu.temp_celsius, 100)}%"></div>
                    </div>
                </div>
                <div class="metric">
                    <span class="metric-label">Memória</span>
                    <span class="metric-value">${memoryPercent}%</span>
                    <div class="metric-sub">${gpu.mem_used_mb.toFixed(0)}MB / ${gpu.mem_total_mb.toFixed(0)}MB</div>
                    <div class="metric-bar">
                        <div class="metric-bar-fill ${memoryPercent > 90 ? 'critical' : ''}" 
                             style="width: ${memoryPercent}%"></div>
                    </div>
                </div>
                <div class="metric">
                    <span class="metric-label">Potência</span>
                    <span class="metric-value">${gpu.power_watts}W</span>
                    <div class="metric-bar">
                        <div class="metric-bar-fill" 
                             style="width: ${Math.min(gpu.power_watts / 3, 100)}%"></div>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }
    
    updateGPUCardContent(card, gpu) {
        const memoryPercent = (gpu.mem_used_mb / gpu.mem_total_mb * 100).toFixed(1);
        const isHighTemp = gpu.temp_celsius > 80;
        const isHighUtil = gpu.util_percent > 90;
        
        // Atualiza status da GPU
        const statusElement = card.querySelector('.gpu-status');
        statusElement.className = `gpu-status ${gpu.util_percent > 0 ? 'active' : 'inactive'}`;
        statusElement.textContent = gpu.util_percent > 0 ? 'Ativa' : 'Inativa';
        
        // Atualiza métricas
        const metrics = card.querySelectorAll('.metric');
        
        // Utilização
        const utilMetric = metrics[0];
        utilMetric.querySelector('.metric-value').textContent = `${gpu.util_percent}%`;
        const utilBarFill = utilMetric.querySelector('.metric-bar-fill');
        utilBarFill.style.width = `${gpu.util_percent}%`;
        utilBarFill.className = `metric-bar-fill ${isHighUtil ? 'critical' : ''}`;
        
        // Temperatura
        const tempMetric = metrics[1];
        tempMetric.querySelector('.metric-value').textContent = `${gpu.temp_celsius}°C`;
        const tempBarFill = tempMetric.querySelector('.metric-bar-fill');
        tempBarFill.style.width = `${Math.min(gpu.temp_celsius, 100)}%`;
        tempBarFill.className = `metric-bar-fill ${isHighTemp ? 'critical' : ''}`;
        
        // Memória
        const memMetric = metrics[2];
        memMetric.querySelector('.metric-value').textContent = `${memoryPercent}%`;
        memMetric.querySelector('.metric-sub').textContent = `${gpu.mem_used_mb.toFixed(0)}MB / ${gpu.mem_total_mb.toFixed(0)}MB`;
        const memBarFill = memMetric.querySelector('.metric-bar-fill');
        memBarFill.style.width = `${memoryPercent}%`;
        memBarFill.className = `metric-bar-fill ${memoryPercent > 90 ? 'critical' : ''}`;
        
        // Potência
        const powerMetric = metrics[3];
        powerMetric.querySelector('.metric-value').textContent = `${gpu.power_watts}W`;
        const powerBarFill = powerMetric.querySelector('.metric-bar-fill');
        powerBarFill.style.width = `${Math.min(gpu.power_watts / 3, 100)}%`;
    }
    
    initializeCharts() {
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'nearest', intersect: false },
            plugins: {
                legend: { 
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        color: '#e6edf3'
                    }
                },
                title: { display: false }
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'minute' },
                    ticks: { 
                        maxTicksLimit: 10,
                        color: '#7a8899'
                    },
                    grid: {
                        color: '#1e2732'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: { 
                        precision: 0,
                        color: '#7a8899'
                    },
                    grid: {
                        color: '#1e2732'
                    }
                }
            },
            elements: {
                point: { radius: 0 },
                line: { tension: 0.1, borderWidth: 2 }
            }
        };
        
        // Inicializa gráfico principal
        this.mainChart = new Chart(
            document.getElementById('main-chart').getContext('2d'),
            {
                type: 'line',
                data: { datasets: [] },
                options: chartOptions
            }
        );
        
        // Inicializa dados dos gráficos
        this.chartData = {
            utilization: {},
            temperature: {},
            memory: {},
            power: {}
        };
        
        // Carrega presets e popula interface
        this.populatePresetSelector();
        this.setupChartEventListeners();
    }
    
    updateCharts(gpuDataList) {
        if (this.chartsPaused) return;
        
        const now = new Date();
        
        // Atualiza dados para todas as métricas
        gpuDataList.forEach(gpu => {
            const gpuId = `gpu_${gpu.device_index}`;
            
            // Inicializa arrays se não existirem
            if (!this.chartData.utilization[gpuId]) {
                this.chartData.utilization[gpuId] = [];
                this.chartData.temperature[gpuId] = [];
                this.chartData.memory[gpuId] = [];
                this.chartData.power[gpuId] = [];
            }
            
            // Adiciona novos pontos
            this.chartData.utilization[gpuId].push({ x: now, y: gpu.util_percent });
            this.chartData.temperature[gpuId].push({ x: now, y: gpu.temp_celsius });
            this.chartData.memory[gpuId].push({ x: now, y: gpu.mem_used_mb });
            this.chartData.power[gpuId].push({ x: now, y: gpu.power_watts });
            
            // Remove pontos antigos
            Object.keys(this.chartData).forEach(metric => {
                if (this.chartData[metric][gpuId].length > this.maxDataPoints) {
                    this.chartData[metric][gpuId].shift();
                }
            });
        });
        
        // Atualiza gráfico principal baseado na configuração atual
        this.updateMainChart();
    }
    
    toggleCharts() {
        this.chartsPaused = !this.chartsPaused;
        const btn = document.getElementById('pause-charts');
        btn.textContent = this.chartsPaused ? '▶️ Retomar' : '⏸️ Pausar';
        btn.className = this.chartsPaused ? 'btn btn-small btn-primary' : 'btn btn-small';
        
        this.log(`Gráficos ${this.chartsPaused ? 'pausados' : 'retomados'}`, 'info');
    }
    
    clearChartData() {
        this.chartData = {
            utilization: {},
            temperature: {},
            memory: {},
            power: {}
        };
        
        if (this.mainChart) {
            this.mainChart.data.datasets = [];
            this.mainChart.update();
        }
        
        this.log('Dados dos gráficos limpos', 'info');
    }
    
    // Novas funções para o gráfico dinâmico
    setupChartEventListeners() {
        // Event listeners para checkboxes de métricas
        document.querySelectorAll('.metric-checkbox input').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateChartConfig());
        });
        
        // Event listeners para seleção de GPUs (será populado dinamicamente)
        this.updateGPUSelector();
    }
    
    updateGPUSelector() {
        const container = document.getElementById('gpu-selector');
        const availableGPUs = new Set();
        
        // Coleta todas as GPUs disponíveis dos dados
        Object.keys(this.chartData.utilization).forEach(gpuId => {
            const gpuIndex = gpuId.split('_')[1];
            availableGPUs.add(gpuIndex);
        });
        
        container.innerHTML = '';
        availableGPUs.forEach(gpuIndex => {
            const label = document.createElement('label');
            label.className = 'gpu-checkbox';
            label.innerHTML = `
                <input type="checkbox" value="${gpuIndex}" checked>
                <span class="gpu-label">GPU ${gpuIndex}</span>
            `;
            
            label.querySelector('input').addEventListener('change', () => this.updateChartConfig());
            container.appendChild(label);
        });
        
        // Atualiza configuração inicial
        this.updateChartConfig();
    }
    
    updateChartConfig() {
        // Coleta métricas selecionadas
        const selectedMetrics = [];
        document.querySelectorAll('.metric-checkbox input:checked').forEach(checkbox => {
            selectedMetrics.push(checkbox.value);
        });
        
        // Coleta GPUs selecionadas
        const selectedGPUs = [];
        document.querySelectorAll('.gpu-checkbox input:checked').forEach(checkbox => {
            selectedGPUs.push(checkbox.value);
        });
        
        this.chartConfig.selectedMetrics = selectedMetrics;
        this.chartConfig.selectedGPUs = selectedGPUs;
        
        this.updateMainChart();
    }
    
    updateMainChart() {
        if (!this.mainChart) return;
        
        const datasets = [];
        const colors = {
            utilization: '#2f81f7',
            temperature: '#f0ad4e', 
            memory: '#3ddc97',
            power: '#ff6b6b'
        };
        
        const units = {
            utilization: '%',
            temperature: '°C',
            memory: 'MB',
            power: 'W'
        };
        
        // Gera datasets baseado na configuração
        this.chartConfig.selectedMetrics.forEach(metric => {
            this.chartConfig.selectedGPUs.forEach(gpuIndex => {
                const gpuId = `gpu_${gpuIndex}`;
                if (this.chartData[metric][gpuId]) {
                    datasets.push({
                        label: `GPU ${gpuIndex} - ${this.getMetricDisplayName(metric)}`,
                        data: this.chartData[metric][gpuId],
                        borderColor: colors[metric],
                        backgroundColor: colors[metric] + '20',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: metric // Permite eixos Y separados se necessário
                    });
                }
            });
        });
        
        this.mainChart.data.datasets = datasets;
        
        // Atualiza configuração do eixo Y
        this.updateYAxisConfiguration();
        
        this.mainChart.update('none');
    }
    
    getMetricDisplayName(metric) {
        const names = {
            utilization: 'Utilização',
            temperature: 'Temperatura',
            memory: 'Memória',
            power: 'Potência'
        };
        return names[metric] || metric;
    }
    
    updateYAxisConfiguration() {
        const yAxisConfig = this.mainChart.options.scales.y;
        
        if (this.chartConfig.yAxisMode === 'auto') {
            yAxisConfig.min = undefined;
            yAxisConfig.max = undefined;
        } else {
            yAxisConfig.min = this.chartConfig.yAxisMin;
            yAxisConfig.max = this.chartConfig.yAxisMax;
        }
    }
    
    toggleYAxisMode() {
        const mode = document.querySelector('input[name="y-axis-mode"]:checked').value;
        this.chartConfig.yAxisMode = mode;
        
        const manualInputs = document.querySelector('.manual-axis-inputs');
        if (mode === 'manual') {
            manualInputs.style.display = 'flex';
        } else {
            manualInputs.style.display = 'none';
        }
        
        this.updateMainChart();
    }
    
    updateYAxisRange() {
        if (this.chartConfig.yAxisMode === 'manual') {
            this.chartConfig.yAxisMin = parseFloat(document.getElementById('y-axis-min').value) || 0;
            this.chartConfig.yAxisMax = parseFloat(document.getElementById('y-axis-max').value) || 100;
            this.updateMainChart();
        }
    }
    
    // Sistema de Presets
    savePreset() {
        const name = document.getElementById('preset-name').value.trim();
        if (!name) {
            this.log('Nome do preset é obrigatório', 'warning');
            return;
        }
        
        const preset = {
            selectedMetrics: [...this.chartConfig.selectedMetrics],
            selectedGPUs: [...this.chartConfig.selectedGPUs],
            yAxisMode: this.chartConfig.yAxisMode,
            yAxisMin: this.chartConfig.yAxisMin,
            yAxisMax: this.chartConfig.yAxisMax,
            timestamp: new Date().toISOString()
        };
        
        this.presets[name] = preset;
        localStorage.setItem('chart-presets', JSON.stringify(this.presets));
        
        this.populatePresetSelector();
        document.getElementById('preset-name').value = '';
        this.log(`Preset "${name}" salvo`, 'success');
    }
    
    loadPreset() {
        const selectedPreset = document.getElementById('preset-selector').value;
        if (!selectedPreset || !this.presets[selectedPreset]) {
            this.log('Selecione um preset válido', 'warning');
            return;
        }
        
        const preset = this.presets[selectedPreset];
        
        // Aplica configuração do preset
        this.chartConfig = { ...preset };
        
        // Atualiza interface
        this.applyPresetToUI(preset);
        
        // Atualiza gráfico
        this.updateMainChart();
        
        this.log(`Preset "${selectedPreset}" carregado`, 'success');
    }
    
    deletePreset() {
        const selectedPreset = document.getElementById('preset-selector').value;
        if (!selectedPreset || !this.presets[selectedPreset]) {
            this.log('Selecione um preset válido', 'warning');
            return;
        }
        
        if (confirm(`Tem certeza que deseja deletar o preset "${selectedPreset}"?`)) {
            delete this.presets[selectedPreset];
            localStorage.setItem('chart-presets', JSON.stringify(this.presets));
            this.populatePresetSelector();
            this.log(`Preset "${selectedPreset}" deletado`, 'info');
        }
    }
    
    populatePresetSelector() {
        const selector = document.getElementById('preset-selector');
        selector.innerHTML = '<option value="">Selecionar preset...</option>';
        
        Object.keys(this.presets).forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            selector.appendChild(option);
        });
    }
    
    onPresetSelect() {
        const loadBtn = document.getElementById('load-preset');
        const deleteBtn = document.getElementById('delete-preset');
        const selected = document.getElementById('preset-selector').value;
        
        loadBtn.disabled = !selected;
        deleteBtn.disabled = !selected;
    }
    
    applyPresetToUI(preset) {
        // Atualiza checkboxes de métricas
        document.querySelectorAll('.metric-checkbox input').forEach(checkbox => {
            checkbox.checked = preset.selectedMetrics.includes(checkbox.value);
        });
        
        // Atualiza checkboxes de GPUs
        document.querySelectorAll('.gpu-checkbox input').forEach(checkbox => {
            checkbox.checked = preset.selectedGPUs.includes(checkbox.value);
        });
        
        // Atualiza modo do eixo Y
        document.querySelector(`input[name="y-axis-mode"][value="${preset.yAxisMode}"]`).checked = true;
        this.toggleYAxisMode();
        
        // Atualiza valores do eixo Y
        document.getElementById('y-axis-min').value = preset.yAxisMin;
        document.getElementById('y-axis-max').value = preset.yAxisMax;
    }
    
    switchTab(tabName) {
        // Atualiza botões
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Atualiza conteúdo
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Carrega dados específicos da aba
        if (tabName === 'stats' && this.isConnected) {
            this.loadStats();
        } else if (tabName === 'sessions' && this.isConnected) {
            this.loadSessions();
        }
    }
    
    async loadHistory() {
        if (!this.isConnected) {
            this.log('Não conectado ao backend', 'warning');
            return;
        }
        
        try {
            const hours = document.getElementById('history-period').value;
            const deviceIndex = document.getElementById('history-gpu').value;
            
            let url = `${this.backendUrl}/api/gpu/history?hours=${hours}&limit=1000`;
            if (deviceIndex) {
                url += `&device_index=${deviceIndex}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.displayHistoryTable(data.data);
            this.log(`Histórico carregado: ${data.count} registros`, 'success');
            
        } catch (error) {
            this.log(`Erro ao carregar histórico: ${error.message}`, 'error');
        }
    }
    
    displayHistoryTable(data) {
        const container = document.getElementById('history-table');
        
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhum dado encontrado</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.className = 'data-table';
        
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>GPU</th>
                    <th>Utilização (%)</th>
                    <th>Memória (MB)</th>
                    <th>Temperatura (°C)</th>
                    <th>Potência (W)</th>
                </tr>
            </thead>
            <tbody>
                ${data.map(row => `
                    <tr>
                        <td>${new Date(row.timestamp).toLocaleString()}</td>
                        <td>${row.device_index}</td>
                        <td>${row.util_percent}%</td>
                        <td>${row.mem_used_mb.toFixed(0)} / ${row.mem_total_mb.toFixed(0)}</td>
                        <td>${row.temp_celsius}°C</td>
                        <td>${row.power_watts}W</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        
        container.innerHTML = '';
        container.appendChild(table);
    }
    
    async loadStats() {
        if (!this.isConnected) return;
        
        try {
            const response = await fetch(`${this.backendUrl}/api/gpu/stats`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.displayStats(data);
            
        } catch (error) {
            this.log(`Erro ao carregar estatísticas: ${error.message}`, 'error');
        }
    }
    
    displayStats(data) {
        const container = document.getElementById('stats-content');
        
        if (!data.devices || data.devices.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhuma estatística disponível</p>';
            return;
        }
        
        const statsHtml = `
            <div class="stats-summary">
                <h3>Resumo (${data.period_hours}h)</h3>
                <p>Total de amostras: <strong>${data.total_samples}</strong></p>
            </div>
            
            <div class="stats-grid">
                ${data.devices.map(device => `
                    <div class="stat-card">
                        <h4>GPU ${device.device_index}</h4>
                        <div class="stat-value">${device.utilization.avg.toFixed(1)}<span class="stat-unit">%</span></div>
                        <div class="stat-range">Utilização (${device.utilization.min}% - ${device.utilization.max}%)</div>
                    </div>
                    
                    <div class="stat-card">
                        <h4>Temperatura Média</h4>
                        <div class="stat-value">${device.temperature_celsius.avg.toFixed(1)}<span class="stat-unit">°C</span></div>
                        <div class="stat-range">${device.temperature_celsius.min}°C - ${device.temperature_celsius.max}°C</div>
                    </div>
                    
                    <div class="stat-card">
                        <h4>Potência Média</h4>
                        <div class="stat-value">${device.power_watts.avg.toFixed(1)}<span class="stat-unit">W</span></div>
                        <div class="stat-range">${device.power_watts.min}W - ${device.power_watts.max}W</div>
                    </div>
                    
                    <div class="stat-card">
                        <h4>Memória Média</h4>
                        <div class="stat-value">${(device.memory_used_mb.avg / 1024).toFixed(1)}<span class="stat-unit">GB</span></div>
                        <div class="stat-range">${device.sample_count} amostras</div>
                    </div>
                `).join('')}
            </div>
        `;
        
        container.innerHTML = statsHtml;
    }
    
    async populateHistoryGPUSelect() {
        if (!this.isConnected) return;
        
        try {
            const response = await fetch(`${this.backendUrl}/api/health`);
            if (!response.ok) return;
            
            const data = await response.json();
            const select = document.getElementById('history-gpu');
            
            // Limpa opções existentes (exceto "Todas as GPUs")
            select.innerHTML = '<option value="">Todas as GPUs</option>';
            
            // Adiciona opção para cada GPU
            for (let i = 0; i < data.gpu_count; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = `GPU ${i}`;
                select.appendChild(option);
            }
            
        } catch (error) {
            console.error('Erro ao popular select de GPUs:', error);
        }
    }
    
    log(message, level = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = { timestamp, level, message };
        
        this.logs.push(logEntry);
        
        // Mantém apenas os últimos 1000 logs
        if (this.logs.length > 1000) {
            this.logs.shift();
        }
        
        // Atualiza container de logs se estiver visível
        if (document.getElementById('logs-tab').classList.contains('active')) {
            this.updateLogContainer();
        }
        
        console.log(`[${timestamp}] ${level.toUpperCase()}: ${message}`);
    }
    
    updateLogContainer() {
        const container = document.getElementById('log-container');
        container.innerHTML = this.logs.map(log => `
            <div class="log-entry">
                <span class="log-timestamp">${log.timestamp}</span>
                <span class="log-level ${log.level}">[${log.level.toUpperCase()}]</span>
                <span class="log-message">${log.message}</span>
            </div>
        `).join('');
        
        // Auto-scroll para o final
        container.scrollTop = container.scrollHeight;
    }
    
    clearLogs() {
        this.logs = [];
        this.updateLogContainer();
    }
    
    exportLogs() {
        const logText = this.logs.map(log => 
            `[${log.timestamp}] ${log.level.toUpperCase()}: ${log.message}`
        ).join('\n');
        
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `gpu-monitor-logs-${new Date().toISOString().slice(0, 19)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.log('Logs exportados', 'info');
    }
    
    // Métodos para gerenciar sessões
    updateSessionButtons() {
        const sessionName = document.getElementById('session-name').value.trim();
        const isConnected = this.isConnected;
        const hasActiveSession = this.currentSession && this.currentSession.session;
        
        document.getElementById('create-session-btn').disabled = !isConnected || !sessionName;
        document.getElementById('start-session-btn').disabled = !isConnected || !sessionName || hasActiveSession;
        document.getElementById('stop-session-btn').disabled = !isConnected || !hasActiveSession;
    }
    
    async createSession() {
        if (!this.isConnected) {
            this.log('Não conectado ao backend', 'warning');
            return;
        }
        
        const sessionName = document.getElementById('session-name').value.trim();
        const sessionDescription = document.getElementById('session-description').value.trim();
        
        if (!sessionName) {
            this.log('Nome da sessão é obrigatório', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`${this.backendUrl}/api/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: sessionName,
                    description: sessionDescription
                })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const sessionData = await response.json();
            this.log(`Sessão criada: ${sessionData.name}`, 'success');
            
            // Limpa o formulário
            document.getElementById('session-name').value = '';
            document.getElementById('session-description').value = '';
            
            // Atualiza a lista de sessões
            await this.loadSessions();
            this.updateSessionButtons();
            
        } catch (error) {
            this.log(`Erro ao criar sessão: ${error.message}`, 'error');
        }
    }
    
    async startSession() {
        if (!this.isConnected) {
            this.log('Não conectado ao backend', 'warning');
            return;
        }
        
        const sessionName = document.getElementById('session-name').value.trim();
        if (!sessionName) {
            this.log('Nome da sessão é obrigatório', 'warning');
            return;
        }
        
        try {
            // Primeiro cria a sessão se não existir
            await this.createSession();
            
            // Encontra a sessão recém-criada
            await this.loadSessions();
            const session = this.sessions.find(s => s.name === sessionName);
            
            if (!session) {
                this.log('Sessão não encontrada', 'error');
                return;
            }
            
            const response = await fetch(`${this.backendUrl}/api/sessions/${session.id}/start`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            this.log(`Gravação iniciada: ${sessionName}`, 'success');
            
        } catch (error) {
            this.log(`Erro ao iniciar gravação: ${error.message}`, 'error');
        }
    }
    
    async stopSession() {
        if (!this.isConnected) {
            this.log('Não conectado ao backend', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`${this.backendUrl}/api/sessions/stop`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            this.log('Gravação finalizada', 'info');
            
        } catch (error) {
            this.log(`Erro ao finalizar gravação: ${error.message}`, 'error');
        }
    }
    
    async loadCurrentSession() {
        if (!this.isConnected) return;
        
        try {
            const response = await fetch(`${this.backendUrl}/api/sessions/current`);
            if (!response.ok) return;
            
            const data = await response.json();
            this.currentSession = data;
            
            const sessionNameElement = document.getElementById('current-session-name');
            if (data.session) {
                sessionNameElement.textContent = data.session.name;
                sessionNameElement.className = 'status-value connected';
            } else {
                sessionNameElement.textContent = 'Nenhuma';
                sessionNameElement.className = 'status-value';
            }
            
        } catch (error) {
            console.error('Erro ao carregar sessão atual:', error);
        }
    }
    
    async loadSessions() {
        if (!this.isConnected) return;
        
        try {
            const response = await fetch(`${this.backendUrl}/api/sessions?limit=50`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.sessions = data.sessions;
            this.displaySessions();
            
        } catch (error) {
            this.log(`Erro ao carregar sessões: ${error.message}`, 'error');
        }
    }
    
    displaySessions() {
        const container = document.getElementById('sessions-list');
        const filter = document.getElementById('sessions-filter').value;
        
        let filteredSessions = this.sessions;
        
        if (filter === 'active') {
            filteredSessions = this.sessions.filter(s => s.is_active);
        } else if (filter === 'completed') {
            filteredSessions = this.sessions.filter(s => !s.is_active);
        }
        
        if (filteredSessions.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhuma sessão encontrada</p>';
            return;
        }
        
        container.innerHTML = filteredSessions.map(session => this.createSessionHTML(session)).join('');
        
        // Adiciona event listeners para as ações
        container.querySelectorAll('.session-action-start').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sessionId = parseInt(e.target.dataset.sessionId);
                this.startExistingSession(sessionId);
            });
        });
        
        container.querySelectorAll('.session-action-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sessionId = parseInt(e.target.dataset.sessionId);
                this.viewSessionData(sessionId);
            });
        });
        
        container.querySelectorAll('.session-action-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sessionId = parseInt(e.target.dataset.sessionId);
                const sessionName = e.target.dataset.sessionName;
                this.deleteSession(sessionId, sessionName);
            });
        });
    }
    
    createSessionHTML(session) {
        const isActive = session.is_active;
        const startTime = session.start_time ? new Date(session.start_time).toLocaleString() : 'N/A';
        const endTime = session.end_time ? new Date(session.end_time).toLocaleString() : 'Em andamento';
        const duration = this.calculateSessionDuration(session);
        
        return `
            <div class="session-item ${isActive ? 'active' : ''}">
                <div class="session-item-header">
                    <h4 class="session-item-title">${session.name}</h4>
                    <span class="session-item-status ${isActive ? 'active' : 'completed'}">
                        ${isActive ? 'Ativa' : 'Finalizada'}
                    </span>
                </div>
                
                ${session.description ? `<div class="session-item-description">${session.description}</div>` : ''}
                
                <div class="session-item-meta">
                    <div class="session-item-stats">
                        <span>📊 ${session.measurement_count} medições</span>
                        <span>⏱️ ${duration}</span>
                        <span>📅 ${startTime}</span>
                    </div>
                    <div class="session-item-actions">
                        ${!isActive ? `<button class="btn btn-success session-action-start" data-session-id="${session.id}">▶️ Iniciar</button>` : ''}
                        <button class="btn btn-primary session-action-view" data-session-id="${session.id}">👁️ Ver Dados</button>
                        <button class="btn btn-danger session-action-delete" data-session-id="${session.id}" data-session-name="${session.name}">🗑️ Deletar</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    calculateSessionDuration(session) {
        if (!session.start_time) return 'N/A';
        
        const start = new Date(session.start_time);
        const end = session.end_time ? new Date(session.end_time) : new Date();
        const diffMs = end - start;
        
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        
        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }
    
    async startExistingSession(sessionId) {
        try {
            const response = await fetch(`${this.backendUrl}/api/sessions/${sessionId}/start`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            this.log(`Sessão ${sessionId} iniciada`, 'success');
            
        } catch (error) {
            this.log(`Erro ao iniciar sessão: ${error.message}`, 'error');
        }
    }
    
    async viewSessionData(sessionId) {
        try {
            const response = await fetch(`${this.backendUrl}/api/sessions/${sessionId}/data`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.displaySessionDataModal(sessionId, data.data);
            
        } catch (error) {
            this.log(`Erro ao carregar dados da sessão: ${error.message}`, 'error');
        }
    }
    
    displaySessionDataModal(sessionId, data) {
        // Por simplicidade, vamos mostrar um alert com estatísticas básicas
        // Em uma implementação completa, seria melhor criar um modal
        const session = this.sessions.find(s => s.id === sessionId);
        const sessionName = session ? session.name : `Sessão ${sessionId}`;
        
        if (data.length === 0) {
            alert(`${sessionName}\n\nNenhum dado de medição encontrado.`);
            return;
        }
        
        // Calcula estatísticas básicas
        const gpus = [...new Set(data.map(d => d.device_index))];
        const startTime = new Date(data[0].timestamp).toLocaleString();
        const endTime = new Date(data[data.length - 1].timestamp).toLocaleString();
        
        const avgUtil = data.reduce((sum, d) => sum + d.util_percent, 0) / data.length;
        const maxTemp = Math.max(...data.map(d => d.temp_celsius));
        const avgPower = data.reduce((sum, d) => sum + d.power_watts, 0) / data.length;
        
        const stats = `${sessionName}\n\n` +
                     `📊 Estatísticas:\n` +
                     `• ${data.length} medições\n` +
                     `• ${gpus.length} GPU(s): ${gpus.join(', ')}\n` +
                     `• Utilização média: ${avgUtil.toFixed(1)}%\n` +
                     `• Temperatura máxima: ${maxTemp.toFixed(1)}°C\n` +
                     `• Potência média: ${avgPower.toFixed(1)}W\n\n` +
                     `📅 Período:\n` +
                     `• Início: ${startTime}\n` +
                     `• Fim: ${endTime}`;
        
        alert(stats);
    }
    
    async deleteSession(sessionId, sessionName) {
        if (!confirm(`Tem certeza que deseja deletar a sessão "${sessionName}"?\n\nTodos os dados de medição serão perdidos permanentemente.`)) {
            return;
        }
        
        try {
            const response = await fetch(`${this.backendUrl}/api/sessions/${sessionId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            this.log(`Sessão "${sessionName}" deletada`, 'info');
            await this.loadSessions();
            await this.loadCurrentSession();
            this.updateSessionButtons();
            
        } catch (error) {
            this.log(`Erro ao deletar sessão: ${error.message}`, 'error');
        }
    }
    
    filterSessions() {
        this.displaySessions();
    }
}

// Inicializa o dashboard quando a página carrega
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new GPUDashboard();
});
