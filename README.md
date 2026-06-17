# Practica PP - Booking con agente IA

Proyecto Django REST para un sistema de booking con agente integrado.

## Ejecutar

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver 127.0.0.1:8000
```

## Agente

Endpoint principal:

```http
POST http://127.0.0.1:8000/api/agent/chat/
```

Ejemplo:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Hay propiedades disponibles del 20 al 25 de julio para 2 personas?\"}"
```

## Entrega

- Documentacion, diagrama Mermaid y prompt: `docs/agent_entrega.md`
- Configuracion opcional Dify/Botpress: `docs/dify_botpress_config.md`
- Guion para video de 3 minutos: `docs/video_guion.md`
- Video demostrativo generado: `docs/video_demo.mp4`
- Requests de prueba: `docs/demo_requests.http`
- Script de demo: `scripts/demo_agent.ps1`

## Verificacion

```powershell
python manage.py check
python manage.py test presupuesto
```
