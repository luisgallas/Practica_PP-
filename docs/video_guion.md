# Guion para video de 3 minutos

Tambien queda generado un video demostrativo en `docs/video_demo.mp4` (aprox. 3 minutos y 20 segundos). Si se quiere regenerar:

```powershell
python scripts/generate_demo_video.py
```

## 0:00 - 0:25 Presentacion

Mostrar el repositorio y explicar:

- Es un proyecto Django de booking.
- Se agrego un agente en `/api/agent/chat/`.
- El agente usa datos reales de propiedades, reservas y amenities.
- Las reservas requieren confirmacion antes de crearse.

## 0:25 - 0:55 Diagrama y configuracion

Abrir `docs/agent_entrega.md` y mostrar el Mermaid:

`Usuario -> Agente -> Backend -> Servicios -> Base de datos`

Mostrar el system prompt en `presupuesto/agent.py` o en la documentacion.

## 0:55 - 1:30 Consulta de disponibilidad

Con el servidor corriendo:

```powershell
python manage.py runserver 127.0.0.1:8000
```

Ejecutar:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Hay propiedades disponibles del 20 al 25 de julio para 2 personas?\"}"
```

Explicar que la respuesta lista propiedades reales y precios estimados desde la base.

## 1:30 - 2:05 Consulta de amenities

Ejecutar:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Que amenities tiene la Quinta Guaira? Acepta mascotas?\"}"
```

Mostrar que responde con amenities reales y aclara mascotas segun lo cargado.

## 2:05 - 2:40 Reserva con confirmacion

Ejecutar:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Quiero reservar esta propiedad para el 15 de agosto en la Quinta Guaira\",\"user_id\":6}"
```

Mostrar que no crea aun la reserva. Devuelve `pending_action` y pregunta si confirma.

Opcionalmente confirmar con el JSON de `pending_action` para demostrar la creacion real.

## 2:40 - 3:00 Anfitrion y cierre

Ejecutar:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" -H "Content-Type: application/json" -d "{\"message\":\"Hay reservas pendientes de confirmar?\",\"user_id\":2}"
```

Cerrar mostrando:

- endpoints conectados;
- tests pasando con `python manage.py test presupuesto`;
- documentacion de Dify/Botpress en `docs/dify_botpress_config.md`.
