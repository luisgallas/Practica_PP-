$ErrorActionPreference = "Stop"

Write-Host "1) Disponibilidad directa"
curl.exe "http://127.0.0.1:8000/api/availability/?start_date=2026-07-20&end_date=2026-07-25&guests=2"

Write-Host "`n2) Agente: disponibilidad"
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Hay propiedades disponibles del 20 al 25 de julio para 2 personas?\"}"

Write-Host "`n3) Agente: amenities"
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Que amenities tiene la Quinta Guaira? Acepta mascotas?\"}"

Write-Host "`n4) Agente: prepara reserva y pide confirmacion"
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Quiero reservar esta propiedad para el 15 de agosto en la Quinta Guaira\",\"user_id\":6}"

Write-Host "`n5) Agente: anfitrion revisa pendientes"
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Hay reservas pendientes de confirmar?\",\"user_id\":2}"
