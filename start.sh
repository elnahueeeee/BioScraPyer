#!/bin/bash

echo "Iniciando backend con Uvicorn..."
# Levanta el backend en segundo plano
uvicorn main:app --reload &

# Guardamos el PID por si quieres matarlo después
BACKEND_PID=$!

# Espera unos segundos para que levante el backend
sleep 5

echo "Iniciando frontend con React..."
cd noticias-app
npm start &

FRONTEND_PID=$!

echo "Todo listo"
echo "Backend corriendo con PID $BACKEND_PID"
echo "Frontend corriendo con PID $FRONTEND_PID"

# Mantener el script vivo hasta que lo detengas con CTRL+C
wait