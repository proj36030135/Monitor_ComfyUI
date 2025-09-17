@echo off
:: Script para iniciar o GPU Monitor e abrir no navegador
:: Versão batch para Windows

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   GPU Monitor - Inicializador
echo ========================================
echo.

:: Configurações
set BACKEND_DIR=backend
set VIEWER_DIR=viewer
set BACKEND_PORT=8000
set WAIT_TIME=10

:: Verifica se estamos no diretório correto
if not exist "%BACKEND_DIR%" (
    echo ❌ Diretório backend não encontrado!
    echo    Execute este script a partir do diretório raiz do projeto
    pause
    exit /b 1
)

if not exist "%VIEWER_DIR%" (
    echo ❌ Diretório viewer não encontrado!
    echo    Execute este script a partir do diretório raiz do projeto
    pause
    exit /b 1
)

:: Verifica se Python está disponível
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado no PATH!
    echo    Instale o Python e adicione-o ao PATH
    pause
    exit /b 1
)

:: Verifica se o backend já está rodando
echo 🔍 Verificando se o backend já está ativo...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:%BACKEND_PORT%/api/health' -TimeoutSec 3 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if !errorlevel! equ 0 (
    echo ⚠️  Backend já está rodando em http://localhost:%BACKEND_PORT%
    echo.
    set /p "CHOICE=Deseja abrir apenas o navegador? (S/n): "
    if /i "!CHOICE!" neq "n" if /i "!CHOICE!" neq "nao" (
        goto :open_browser
    )
    exit /b 0
)

:: Inicia o backend em segundo plano
echo 🚀 Iniciando backend...
cd /d "%BACKEND_DIR%"
start /b "GPU Monitor Backend" python server.py
cd /d ..

:: Aguarda o backend inicializar
echo ⏳ Aguardando backend inicializar (%WAIT_TIME% segundos)...
timeout /t %WAIT_TIME% /nobreak >nul

:: Verifica se o backend está respondendo
echo 🔍 Verificando se backend está ativo...
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:%BACKEND_PORT%/api/health' -TimeoutSec 5 -UseBasicParsing | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if !errorlevel! neq 0 (
    echo ❌ Backend não conseguiu inicializar!
    echo    Verifique se as dependências estão instaladas:
    echo    pip install -r backend/requirements.txt
    pause
    exit /b 1
)

echo ✅ Backend está ativo!

:open_browser
:: Abre o navegador com a interface
echo 🌐 Abrindo navegador...
set "FRONTEND_PATH=%CD%\%VIEWER_DIR%\index.html"

if not exist "!FRONTEND_PATH!" (
    echo ❌ Interface não encontrada: !FRONTEND_PATH!
    pause
    exit /b 1
)

:: Abre no navegador padrão
start "" "!FRONTEND_PATH!"

echo.
echo ✅ Aplicação iniciada com sucesso!
echo.
echo 🔗 Backend:  http://localhost:%BACKEND_PORT%
echo 🌐 Frontend: file:///!FRONTEND_PATH!
echo.
echo 💡 Dicas:
echo    - O backend roda em segundo plano
echo    - Feche esta janela para manter o backend ativo
echo    - Para parar completamente, use Ctrl+C ou feche o terminal
echo.

:: Mantém a janela aberta
echo Pressione qualquer tecla para fechar este launcher...
echo (O backend continuará rodando em segundo plano)
pause >nul

endlocal
