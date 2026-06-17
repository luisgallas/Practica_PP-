# Configuracion opcional para Dify o Botpress

Esta entrega ya incluye el agente en el backend (`POST /api/agent/chat/`). Si se quiere mostrar la conexion desde Dify Cloud o Botpress, se puede configurar el bot como cliente HTTP de estos endpoints.

## System prompt

Usar el mismo prompt de `presupuesto/agent.py`:

```text
Sos el asistente de reservas de GuairaDevs Booking. Ayudas a huespedes a consultar
propiedades, amenities, resenas, disponibilidad y reservas; y ayudas a anfitriones a revisar
sus reservas. No respondes temas fuera de la plataforma. No buscas online: solo usas
la informacion disponible en la API/backend del proyecto. Si falta un dato, lo pedis.
Antes de crear, confirmar, cancelar o modificar una reserva, siempre pedis confirmacion
explicita y mostras el resumen de la accion.
```

## Tools HTTP sugeridas

### Consultar disponibilidad

- Method: `GET`
- URL: `http://127.0.0.1:8000/api/availability/`
- Query params:
  - `start_date`: fecha inicio `YYYY-MM-DD`
  - `end_date`: fecha fin `YYYY-MM-DD`
  - `guests`: cantidad de huespedes

### Consultar propiedades

- Method: `GET`
- URL: `http://127.0.0.1:8000/api/properties/`

### Listar reservas del anfitrion

- Method: `GET`
- URL: `http://127.0.0.1:8000/api/reservations/`
- Query params:
  - `host_id`
  - `status`
  - `month`

### Crear reserva

- Method: `POST`
- URL: `http://127.0.0.1:8000/api/reservations/`
- Body:

```json
{
  "id_propiedad": 9,
  "id_huesped": 6,
  "fecha_inicio": "2026-08-15",
  "fecha_fin": "2026-08-16",
  "cantidad_huespedes": 1
}
```

Regla obligatoria del bot: antes de llamar este endpoint, pedir confirmacion explicita al usuario.

## Alternativa mas simple

Configurar un unico nodo HTTP:

- Method: `POST`
- URL: `http://127.0.0.1:8000/api/agent/chat/`
- Body:

```json
{
  "message": "{{user.message}}",
  "user_id": "{{user.id}}",
  "confirm": false,
  "pending_action": "{{conversation.pending_action}}"
}
```

El backend ya maneja intenciones, datos reales, errores y confirmacion.
