@echo off
REM Quick setup script for AI conversations (ChatGPT + Gemini)
REM For Windows CMD/PowerShell

echo ========================================
echo AI Conversation Script Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Installing required packages...
python -m pip install -q -r ai_conversation_requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)
echo ✓ Packages installed

echo.
echo [2/3] API Key Configuration
echo.
echo You need at least one API key. Get them from:
echo   - OpenAI (ChatGPT): https://platform.openai.com/api-keys
echo   - Google Gemini:    https://aistudio.google.com/app/apikey
echo.

set /p OPENAI_KEY="Enter OpenAI API key (or press Enter to skip): "
set /p GEMINI_KEY="Enter Gemini API key (or press Enter to skip): "

if "%OPENAI_KEY%"=="" if "%GEMINI_KEY%"=="" (
    echo ERROR: At least one API key is required
    pause
    exit /b 1
)

if not "%OPENAI_KEY%"=="" (
    set OPENAI_API_KEY=%OPENAI_KEY%
    echo ✓ OpenAI key configured
)

if not "%GEMINI_KEY%"=="" (
    set GEMINI_API_KEY=%GEMINI_KEY%
    echo ✓ Gemini key configured
)

echo.
echo [3/3] Ready to run!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Edit ai_conversation.py and replace the initial_topic with your tech brief
echo 2. Or use the tech_brief_template.md as a starting point
echo 3. Run: python ai_conversation.py
echo.
echo Press any key to run the script now, or Ctrl+C to exit...
pause >nul

python ai_conversation.py
