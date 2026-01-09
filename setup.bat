@echo off
REM MemU MCP Server - Windows Installation Script
REM This script automates the Docker-based installation of MemU MCP Server

setlocal enabledelayedexpansion

REM Configuration
set IMAGE_NAME=memu-mcp-server
set CONTAINER_NAME=memu-mcp
set DATA_DIR=%USERPROFILE%\.memu\data
set CONFIG_DIR=%USERPROFILE%\.memu

echo.
echo ==========================================
echo MemU MCP Server - Automated Installer
echo ==========================================
echo.

REM Check if Docker is installed
echo [INFO] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [SUCCESS] Docker is installed and running
echo.

REM Create directories
echo [INFO] Creating directories...
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
echo [SUCCESS] Directories created at %CONFIG_DIR%
echo.

REM Create .env file
set ENV_FILE=%CONFIG_DIR%\.env

if exist "%ENV_FILE%" (
    echo [WARNING] .env file already exists at %ENV_FILE%
    set /p OVERWRITE="Do you want to overwrite it? (y/N): "
    if /i not "!OVERWRITE!"=="y" (
        echo [INFO] Keeping existing .env file
        goto :build_image
    )
)

echo [INFO] Creating .env file...
echo.
echo Select your LLM provider:
echo 1) Ollama (Local)
echo 2) LMStudio (Local)
echo 3) OpenRouter
echo 4) DeepInfra
echo 5) Fireworks AI
echo 6) OpenAI
echo 7) Custom
echo.
set /p PROVIDER_CHOICE="Enter choice (1-7): "

if "%PROVIDER_CHOICE%"=="1" (
    set PROVIDER=ollama
    set BASE_URL=http://host.docker.internal:11434/v1
    set /p MODEL="Enter Ollama model name [llama3]: "
    if "!MODEL!"=="" set MODEL=llama3
    set API_KEY=ollama
) else if "%PROVIDER_CHOICE%"=="2" (
    set PROVIDER=lmstudio
    set BASE_URL=http://host.docker.internal:1234/v1
    set /p MODEL="Enter LMStudio model name [local-model]: "
    if "!MODEL!"=="" set MODEL=local-model
    set API_KEY=lm-studio
) else if "%PROVIDER_CHOICE%"=="3" (
    set PROVIDER=openrouter
    set BASE_URL=https://openrouter.ai/api/v1
    set /p API_KEY="Enter OpenRouter API key: "
    set /p MODEL="Enter model name [anthropic/claude-3.5-sonnet]: "
    if "!MODEL!"=="" set MODEL=anthropic/claude-3.5-sonnet
) else if "%PROVIDER_CHOICE%"=="4" (
    set PROVIDER=deepinfra
    set BASE_URL=https://api.deepinfra.com/v1/openai
    set /p API_KEY="Enter DeepInfra API key: "
    set /p MODEL="Enter model name [meta-llama/Meta-Llama-3.1-70B-Instruct]: "
    if "!MODEL!"=="" set MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct
) else if "%PROVIDER_CHOICE%"=="5" (
    set PROVIDER=fireworks
    set BASE_URL=https://api.fireworks.ai/inference/v1
    set /p API_KEY="Enter Fireworks AI API key: "
    set /p MODEL="Enter model name [accounts/fireworks/models/llama-v3p1-70b-instruct]: "
    if "!MODEL!"=="" set MODEL=accounts/fireworks/models/llama-v3p1-70b-instruct
) else if "%PROVIDER_CHOICE%"=="6" (
    set PROVIDER=openai
    set BASE_URL=https://api.openai.com/v1
    set /p API_KEY="Enter OpenAI API key: "
    set /p MODEL="Enter chat model [gpt-4o-mini]: "
    if "!MODEL!"=="" set MODEL=gpt-4o-mini
) else if "%PROVIDER_CHOICE%"=="7" (
    set PROVIDER=custom
    set /p BASE_URL="Enter base URL: "
    set /p API_KEY="Enter API key: "
    set /p MODEL="Enter model name: "
) else (
    echo [ERROR] Invalid choice
    pause
    exit /b 1
)

REM Create .env file
(
    echo # MemU MCP Server Configuration
    echo MEMU_PROVIDER=!PROVIDER!
    echo.
    echo # LLM Configuration
    echo LLM_BASE_URL=!BASE_URL!
    echo LLM_API_KEY=!API_KEY!
    echo LLM_CHAT_MODEL=!MODEL!
    echo LLM_EMBED_MODEL=!MODEL!
    echo.
    echo # Database Configuration
    echo DB_PROVIDER=inmemory
    echo.
    echo # Retrieval Configuration
    echo RETRIEVE_METHOD=rag
) > "%ENV_FILE%"

echo [SUCCESS] .env file created at %ENV_FILE%
echo.

:build_image
REM Build Docker image
echo [INFO] Building Docker image...
docker build -t %IMAGE_NAME% .
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    pause
    exit /b 1
)
echo [SUCCESS] Docker image built successfully
echo.

REM Ask if user wants to run container
set /p RUN_NOW="Do you want to run the container now? (y/N): "
if /i not "!RUN_NOW!"=="y" (
    echo [INFO] Skipping container run. You can run it later with:
    echo   docker run -d --name %CONTAINER_NAME% --env-file "%ENV_FILE%" -v "%DATA_DIR%:/data" %IMAGE_NAME%
    goto :show_usage
)

REM Run container
echo [INFO] Running container...

REM Stop existing container if running
docker ps -a --format "{{.Names}}" | findstr /x "%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Stopping existing container...
    docker stop %CONTAINER_NAME% >nul 2>&1
    docker rm %CONTAINER_NAME% >nul 2>&1
)

docker run -d --name %CONTAINER_NAME% --env-file "%ENV_FILE%" -v "%DATA_DIR%:/data" %IMAGE_NAME%
if errorlevel 1 (
    echo [ERROR] Failed to run container
    pause
    exit /b 1
)

echo [SUCCESS] Container is running as %CONTAINER_NAME%
echo.

:show_usage
echo.
echo ==========================================
echo MemU MCP Server Installation Complete!
echo ==========================================
echo.
echo Configuration files:
echo   - Config directory: %CONFIG_DIR%
echo   - Data directory: %DATA_DIR%
echo   - Environment file: %ENV_FILE%
echo.
echo Docker container:
echo   - Image: %IMAGE_NAME%
echo   - Container: %CONTAINER_NAME%
echo.
echo Useful commands:
echo   - View logs:        docker logs -f %CONTAINER_NAME%
echo   - Stop server:      docker stop %CONTAINER_NAME%
echo   - Start server:     docker start %CONTAINER_NAME%
echo   - Restart server:   docker restart %CONTAINER_NAME%
echo   - Remove container: docker rm -f %CONTAINER_NAME%
echo.
echo To use with Claude Desktop or other MCP clients,
echo configure them to use stdio transport with this command:
echo   docker run -i --rm --env-file "%ENV_FILE%" -v "%DATA_DIR%:/data" %IMAGE_NAME%
echo.
echo [SUCCESS] Installation complete!
echo.
pause
