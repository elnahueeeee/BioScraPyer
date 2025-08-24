@echo off
echo Iniciando backend con Uvicorn...
start cmd /k "uvicorn main:app --reload"

timeout /t 5 >nul

echo Iniciando frontend con React...
cd noticias-app
start cmd /k "npm start"

echo Todo listo