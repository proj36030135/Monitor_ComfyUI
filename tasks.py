"""Tasks de automação usando Invoke."""

import os
import platform
from invoke import task


@task
def install(ctx):
    """Instala dependências."""
    print("📦 Instalando dependências...")
    ctx.run("pip install -r requirements.txt")


@task(install)
def dev(ctx):
    """Configura ambiente de desenvolvimento."""
    print("🚀 Configurando ambiente de desenvolvimento...")
    ctx.run("alembic upgrade head")
    print("✅ Ambiente pronto para desenvolvimento")


@task
def test(ctx, cov=False):
    """Executa testes."""
    print("🧪 Executando testes...")
    cmd = "pytest -v"
    if cov:
        cmd += " --cov=app --cov-report=html --cov-report=term-missing"
    ctx.run(cmd)


@task
def lint(ctx, fix=False):
    """Executa linting com Ruff."""
    print("🔍 Executando linting...")
    cmd = "ruff check app/ alembic/"
    if fix:
        cmd += " --fix"
    ctx.run(cmd)


@task
def format(ctx, check=False):
    """Formata código com Black."""
    if check:
        print("📋 Verificando formatação...")
        ctx.run("black --check app/ alembic/ tests/")
    else:
        print("🎨 Formatando código...")
        ctx.run("black app/ alembic/ tests/")


@task
def run(ctx, host="127.0.0.1", port="8080", prod=False):
    """Executa servidor."""
    print(f"🌐 Iniciando servidor em http://{host}:{port}")
    
    cmd = f"uvicorn app.main:app --host {host} --port {port}"
    
    if prod:
        cmd += " --workers 1"
        print("🚀 Modo produção")
    else:
        cmd += " --reload"
        print("🔧 Modo desenvolvimento (reload automático)")
    
    ctx.run(cmd)


@task
def migrate(ctx, message=None, up=False, down=False, history=False):
    """Gerencia migrações do banco de dados."""
    if message:
        print(f"📝 Criando nova migração: {message}")
        ctx.run(f'alembic revision --autogenerate -m "{message}"')
    elif up:
        print("⬆️ Aplicando migrações...")
        ctx.run("alembic upgrade head")
    elif down:
        print("⬇️ Revertendo última migração...")
        ctx.run("alembic downgrade -1")
    elif history:
        print("📜 Histórico de migrações:")
        ctx.run("alembic history")
    else:
        print("❓ Uso: invoke migrate --message='descricao' | --up | --down | --history")


@task
def clean(ctx, db=False):
    """Remove arquivos temporários."""
    print("🧹 Limpando arquivos temporários...")
    
    # Arquivos Python temporários
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "*.egg-info",
    ]
    
    for pattern in patterns:
        try:
            if platform.system() == "Windows":
                # Windows PowerShell
                ctx.run(f'Get-ChildItem -Path . -Recurse -Name "{pattern}" | Remove-Item -Recurse -Force', warn=True)
            else:
                # Unix/Linux
                ctx.run(f'find . -name "{pattern}" -exec rm -rf {{}} +', warn=True)
        except Exception:
            pass  # Ignora erros se arquivo não existir
    
    if db:
        print("🗃️ Removendo arquivos do banco de dados...")
        db_files = ["app.db", "app.db-shm", "app.db-wal"]
        for db_file in db_files:
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"❌ Removido: {db_file}")


@task
def check(ctx):
    """Executa todas as verificações."""
    print("🔍 Executando todas as verificações...")
    lint(ctx)
    format(ctx, check=True) 
    test(ctx)
    print("✅ Todas as verificações passaram!")


@task(clean, install, dev, check)
def setup(ctx):
    """Setup completo do projeto."""
    print("🎉 Setup completo finalizado!")


@task
def health(ctx, host="127.0.0.1", port="8080"):
    """Testa o endpoint de health."""
    import requests
    
    url = f"http://{host}:{port}/health"
    print(f"🏥 Testando health check: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check OK!")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database', {}).get('status')}")
            print(f"   Version: {data.get('version')}")
        else:
            print(f"❌ Health check falhou! Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar: {e}")
        print("💡 Certifique-se de que o servidor está rodando: invoke run")


@task
def docs(ctx, host="127.0.0.1", port="8080"):
    """Abre documentação da API no browser."""
    import webbrowser
    
    url = f"http://{host}:{port}/docs"
    print(f"📚 Abrindo documentação: {url}")
    webbrowser.open(url)
