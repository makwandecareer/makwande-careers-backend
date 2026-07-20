@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-openai-paystack.ps1" -ProjectRoot "%CD%"
if errorlevel 1 pause
