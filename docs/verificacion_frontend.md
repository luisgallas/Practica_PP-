# Verificación de la integración frontend

Fecha de cierre de la verificación: 5 de noviembre de 2026. Se verificó la implementación local, no un despliegue público.

| Comprobación | Resultado |
| --- | --- |
| Django `check` | Sin errores |
| Django `check --deploy` | Sin observaciones con DEBUG=False y una clave aleatoria temporal; no se modificó el entorno de desarrollo |
| Migraciones | Nueva migración aplicada; sin cambios pendientes por generar |
| Pruebas Django | 40 casos: 39 correctos, 1 omitido por requerir PostgreSQL |
| Pruebas frontend | 8 casos correctos con Vitest 4.1.12 |
| TypeScript y build Vite | Compilación de producción correcta |
| Auditoría npm | 0 vulnerabilidades conocidas informadas tras la actualización |
| OpenAPI | Exportado y validado; rutas versionadas |
| HTTP local | Inicio de Vite y catálogo de API respondieron 200 |
| Navegador real | No disponible: el host de acceso al navegador no estaba operativo |
| Lighthouse, axe y revisión visual responsive | Pendientes; no se trasladan puntajes del prototipo anterior |
| Carga y concurrencia en PostgreSQL | Ensayo preparado para CI; no ejecutado localmente |

Las pruebas de backend cubren permisos entre usuarios y roles, datos privados fuera del catálogo, filtros, consultas sin crecimiento por cada tarjeta, creación de reservas con total calculado por servidor, rechazo de solapamientos, capacidad y fechas, transiciones, cancelación, favoritos, reseñas propias, imágenes recodificadas, archivos falsos, límite de tamaño/dimensiones/fotos, portada, CSRF, renovación, revocación, límites de login y suplantación de identidad por chat/API/admin.

Las pruebas frontend cubren asociación de campos y errores accesibles, botón ocupado, reintento, cantidad/tipo/tamaño de fotos, fechas de reserva, invalidación de cotización al cambiar fechas y bloqueo de doble envío. Los casos de interfaz usan datos controlados únicamente dentro de las pruebas; la aplicación utiliza la API real.

Para verificar HTTP se preparó una base independiente `.qa/hospeda.sqlite3`; no se cargaron datos demo sobre la base principal. `.qa` también conserva el respaldo temporal de dependencias previo a la actualización y está ignorado por Git. No contiene entregables que deban publicarse.

La compilación emitió advertencias no bloqueantes sobre anotaciones de optimización en Zod. Node 23.3, instalado en el equipo, genera además advertencias de compatibilidad; el proyecto indica Node 22 LTS para ejecuciones reproducibles. El workflow de GitHub Actions quedó escrito, pero no se ejecutó ni publicó remotamente desde esta sesión.

## Revisión manual pendiente

1. Abrir inicio, resultados, detalle, reserva y paneles en 390, 768 y 1440 px.
2. Recorrer todos los controles usando Tab, Shift+Tab, Enter y Escape; verificar foco y lectores de pantalla.
3. Probar huésped → solicitud → anfitrión → confirmación → cancelación y notificaciones.
4. Publicar un alojamiento con fotos propias, cambiar portada y comprobar el máximo de cinco.
5. Ejecutar axe y Lighthouse por ruta, registrando versión, tamaño de pantalla y condiciones de red.
6. Ejecutar el workflow con PostgreSQL y una prueba de carga representativa antes de dimensionar usuarios simultáneos.
