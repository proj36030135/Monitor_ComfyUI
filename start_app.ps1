# GPU Monitor - Script de Inicialização PowerShell
# Inicia o backend e abre a interface web automaticamente

param(
    [string]$BackendHost = "localhost",
    [int]$BackendPort = 8000,
    [int]$WaitTimeout = 30,
    [switch]$SkipBrowser,
    [switch]$Verbose
)

# Configurações
$BackendDir = "backend"
$ViewerDir = "viewer"
$BackendScript = "server.py"
$FrontendFile = "index.html"

# Função para log com cores
function Write-ColorLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $levelColor = switch ($Level) {
        "INFO" { "Cyan" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    
    Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
    Write-Host "$Level" -NoNewline -ForegroundColor $levelColor
    Write-Host ": $Message" -ForegroundColor $Color
}

# Função para verificar se um processo está rodando na porta
function Test-PortInUse {
    param([int]$Port)
    
    try {
        $connection = Test-NetConnection -ComputerName $BackendHost -Port $Port -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    } catch {
        return $false
    }
}

# Função para verificar saúde do backend
function Test-BackendHealth {
    param([string]$Url)
    
    try {
        $response = Invoke-RestMethod -Uri "$Url/api/health" -Method Get -TimeoutSec 5
        return $true
    } catch {
        if ($Verbose) {
            Write-ColorLog "Health check falhou: $($_.Exception.Message)" "WARNING"
        }
        return $false
    }
}

# Função para aguardar o backend ficar disponível
function Wait-ForBackend {
    param(
        [string]$Url,
        [int]$TimeoutSeconds
    )
    
    Write-ColorLog "Aguardando backend em $Url..."
    
    $startTime = Get-Date
    while (((Get-Date) - $startTime).TotalSeconds -lt $TimeoutSeconds) {
        if (Test-BackendHealth -Url $Url) {
            Write-ColorLog "Backend está respondendo!" "SUCCESS"
            return $true
        }
        Start-Sleep -Seconds 1
    }
    
    Write-ColorLog "Timeout: Backend não respondeu em $TimeoutSeconds segundos" "ERROR"
    return $false
}

# Função principal
function Start-GPUMonitor {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "   GPU Monitor - Inicializador PowerShell" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Verifica se estamos no diretório correto
    if (-not (Test-Path $BackendDir) -or -not (Test-Path $ViewerDir)) {
        Write-ColorLog "Diretórios backend ou viewer não encontrados!" "ERROR"
        Write-ColorLog "Execute este script a partir do diretório raiz do projeto" "ERROR"
        return $false
    }
    
    # Verifica se Python está disponível
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorLog "Python encontrado: $pythonVersion" "SUCCESS"
    } catch {
        Write-ColorLog "Python não encontrado no PATH!" "ERROR"
        Write-ColorLog "Instale o Python e adicione-o ao PATH" "ERROR"
        return $false
    }
    
    $backendUrl = "http://${BackendHost}:${BackendPort}"
    
    # Verifica se o backend já está rodando
    if (Test-BackendHealth -Url $backendUrl) {
        Write-ColorLog "Backend já está rodando em $backendUrl" "WARNING"
        
        if (-not $SkipBrowser) {
            $choice = Read-Host "Deseja abrir apenas o navegador? (S/n)"
            if ($choice -eq "" -or $choice -match "^[SsYy]") {
                Open-Browser
                return $true
            }
        }
        return $true
    }
    
    # Verifica se a porta está em uso por outro processo
    if (Test-PortInUse -Port $BackendPort) {
        Write-ColorLog "Porta $BackendPort está em uso por outro processo!" "ERROR"
        return $false
    }
    
    # Inicia o backend
    Write-ColorLog "Iniciando backend..."
    
    $backendPath = Join-Path $BackendDir $BackendScript
    if (-not (Test-Path $backendPath)) {
        Write-ColorLog "Script do backend não encontrado: $backendPath" "ERROR"
        return $false
    }
    
    try {
        $processInfo = Start-Process -FilePath "python" -ArgumentList $backendPath -WorkingDirectory $BackendDir -PassThru -WindowStyle Hidden
        Write-ColorLog "Backend iniciado com PID: $($processInfo.Id)" "SUCCESS"
        
        # Aguarda o backend ficar disponível
        if (-not (Wait-ForBackend -Url $backendUrl -TimeoutSeconds $WaitTimeout)) {
            Write-ColorLog "Finalizando processo do backend..." "WARNING"
            Stop-Process -Id $processInfo.Id -Force -ErrorAction SilentlyContinue
            return $false
        }
        
        # Abre o navegador se solicitado
        if (-not $SkipBrowser) {
            Open-Browser
        }
        
        # Exibe informações de sucesso
        Write-Host ""
        Write-ColorLog "Aplicação iniciada com sucesso!" "SUCCESS"
        Write-Host ""
        Write-Host "🔗 Backend:  $backendUrl" -ForegroundColor Green
        Write-Host "🌐 Frontend: file:///$((Get-Location).Path)\$ViewerDir\$FrontendFile" -ForegroundColor Green
        Write-Host ""
        Write-Host "💡 Dicas:" -ForegroundColor Yellow
        Write-Host "   - O backend roda em segundo plano (PID: $($processInfo.Id))" -ForegroundColor Gray
        Write-Host "   - Use Ctrl+C para finalizar" -ForegroundColor Gray
        Write-Host "   - A interface atualiza automaticamente" -ForegroundColor Gray
        Write-Host ""
        
        # Aguarda interrupção
        try {
            Write-Host "Pressione Ctrl+C para finalizar a aplicação..."
            while ($true) {
                Start-Sleep -Seconds 1
                if ($processInfo.HasExited) {
                    Write-ColorLog "Backend foi finalizado inesperadamente" "ERROR"
                    break
                }
            }
        } catch {
            Write-ColorLog "Finalizando aplicação..." "WARNING"
        } finally {
            if (-not $processInfo.HasExited) {
                Write-ColorLog "Finalizando backend..." "INFO"
                Stop-Process -Id $processInfo.Id -Force -ErrorAction SilentlyContinue
            }
        }
        
        return $true
        
    } catch {
        Write-ColorLog "Erro ao iniciar backend: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Função para abrir o navegador
function Open-Browser {
    Write-ColorLog "Abrindo navegador..."
    
    $frontendPath = Join-Path (Get-Location) "$ViewerDir\$FrontendFile"
    
    if (-not (Test-Path $frontendPath)) {
        Write-ColorLog "Interface não encontrada: $frontendPath" "ERROR"
        return $false
    }
    
    try {
        Start-Process $frontendPath
        Write-ColorLog "Interface aberta no navegador" "SUCCESS"
        return $true
    } catch {
        Write-ColorLog "Erro ao abrir navegador: $($_.Exception.Message)" "ERROR"
        Write-ColorLog "Abra manualmente: file:///$frontendPath" "INFO"
        return $false
    }
}

# Executa a função principal
if ($MyInvocation.InvocationName -ne '.') {
    Start-GPUMonitor
}
