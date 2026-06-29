# Auditoria de tests para entrega 1.0.0

Fecha de auditoria: 2026-06-29.

## Estado actual

Comandos verificados:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test presupuesto
```

Resultado esperado de la suite actual:

- `python manage.py check`: sin issues.
- `python manage.py makemigrations --check --dry-run`: sin migraciones pendientes.
- `python manage.py test presupuesto`: 9 tests OK.

## Cobertura existente

Los tests actuales cubren:

- Endpoint de disponibilidad con propiedades reales.
- Flujo del agente que pide confirmacion antes de crear reservas.
- Confirmacion de reserva y marcado de fechas como `reservada`.
- Interpretacion de rangos de fechas ISO, slash y texto natural.
- Consulta de reservas pendientes para anfitrion.
- Bloqueo de consulta de anfitrion cuando el usuario tiene rol huesped.
- Consulta global de reservas para administrador.
- Respuesta del agente sobre resenas de una propiedad.

## Refuerzos recomendados

Prioridad alta:

- Test de solapamiento de reservas: una reserva pendiente o confirmada debe impedir una nueva reserva sobre fechas cruzadas.
- Test de liberacion de disponibilidad: al cancelar o rechazar una reserva, las fechas asociadas deben volver a `disponible`.
- Test de validacion de rangos invalidos: `end_date <= start_date` debe devolver error controlado en API y agente.
- Test de propiedad no disponible: propiedades pausadas o inactivas no deben aparecer en disponibilidad ni poder reservarse.
- Test de confirmacion invalida: el agente no debe crear reservas si falta `pending_action` o si el tipo de accion no corresponde.

Prioridad media:

- Test de calculo de precio con dias de semana, fin de semana y tarifa de limpieza.
- Test de normalizacion de amenities para evitar duplicados por mayusculas o acentos.
- Test de filtros de reservas por `host_id`, `status` y `month`.
- Test de permisos/roles de API si se agrega autenticacion real.
- Test de endpoints de detalle de propiedades y listado de amenities.

Prioridad baja:

- Test de textos fuera de alcance para asegurar que el agente no responda temas externos.
- Test de propiedades sin resenas.
- Test de payload serializado de disponibilidades dentro de una reserva.
- Test de idempotencia de `seed_data` para asegurar que se puede correr varias veces sin duplicar datos.

## Riesgos observados

- La suite es buena para demostrar el flujo principal del agente, pero todavia es liviana para reglas de negocio de reservas.
- Falta cobertura especifica de errores HTTP 400 en reservas directas.
- Falta cobertura del admin, aunque eso suele verificarse manualmente para esta clase de entrega.
- Si el proyecto suma autenticacion por token o permisos, la suite deberia ampliarse antes de una version productiva.

## Recomendacion de cierre

Para la entrega academica, la base actual es suficiente si se acompana con la evidencia documental y los comandos de verificacion. Para una version posterior, conviene priorizar primero los tests de solapamiento, cancelacion/liberacion y rangos invalidos.
