# Frontend de Hospeda PY

Esta implementación transforma la propuesta de Hospeda PY en una aplicación React conectada a Django. Incluye búsqueda, reservas y gestión por los tres roles, con fotografías persistentes. El frontend trabaja con la base de datos real de la API; los datos de `seed_data` sirven únicamente para demostración.

## Criterios tomados de los documentos

Se revisaron `Hospeda_PY_Final.docx` y `Presentacion_Propuesta_Inicial.pptx`. Los prompts incluidos en el Word se trataron como evidencia del prototipo anterior. No se ejecutaron como instrucciones ni se conservaron sus respuestas simuladas.

Se adoptó React + Vite + TypeScript, según la decisión explícita de la presentación. Next.js aparece como tecnología del prototipo generado anteriormente. Se conservaron la identidad Hospeda PY, los colores, las reglas de espaciado y el recorrido de búsqueda, detalle, reserva y confirmación del Word. Se sumaron las pantallas necesarias para anfitriones y administradores.

| Propuesta | Implementación |
| --- | --- |
| React, Vite, TypeScript, React Router | SPA independiente en `frontend/`, rutas reales y páginas cargadas bajo demanda |
| Tailwind y Design Tokens | Tailwind 4, `src/tokens.css` y estilos comunes en `src/estilos.css` |
| Axios y TanStack Query | Cliente HTTP, renovación de acceso, caché, cancelación de consultas y actualización tras cambios |
| React Hook Form y Zod | Formularios de ingreso, registro, alojamientos y reserva |
| JWT estándar y OpenAPI | Simple JWT, refresh HttpOnly, Swagger, ReDoc y `docs/openapi.yaml` |
| Cuatro vistas y confirmación | Inicio, resultados, detalle, formulario de reserva y comprobante con identificador real |
| Tres roles | Huésped, anfitrión y administrador, tanto en rutas como en permisos de API |
| Hasta cinco fotos | Selección múltiple, vista previa, publicación, portada y eliminación |
| Favoritos y reseñas | Persisten por usuario; reseñas de estadías propias completadas |
| PostgreSQL y almacenamiento externo | Configuración por entorno; SQLite y disco solo como opciones locales |
| Auditorías Lighthouse del prototipo | No se trasladan a esta implementación: se requieren mediciones propias |

## Organización del código

```text
frontend/
  public/                  Marca, ilustración y marcador de alojamiento sin foto
  src/
    componentes/           Botones, campos, estados, buscador, tarjetas y fotos
    contextos/Sesion.tsx   Identidad actual y ciclo de la sesión
    paginas/               Una página por responsabilidad
    servicios/api.ts       Axios y renovación compartida entre solicitudes
    servicios/formato.ts   Guaraníes, fechas y nombres de tipos
    pruebas/               Pruebas de controles, fotos y reserva integrada
    tipos.ts               Contratos TypeScript
    tokens.css             Valores de diseño del documento
    estilos.css            Componentes y adaptación a pantallas pequeñas
    principal.tsx          Enrutamiento y proveedores
presupuesto/
  api_serializadores.py    Validación de entrada y datos de respuesta
  api_sesion.py            Registro, login, renovación y logout
  api_vistas.py            API de la aplicación web
  api_urls.py              Rutas /api/v1/
  imagenes.py              Decodificación, límites y compresión de imágenes
  test_frontend_api.py     Pruebas de integración y seguridad
```

Los nuevos nombres de variables, funciones, componentes y comentarios se escriben en español donde lo permite el ecosistema. Se mantienen las palabras de los contratos de bibliotecas (`get_queryset`, `useQuery`, `onSuccess`, etc.) y las interfaces anteriores para evitar cambios incompatibles innecesarios.

## Pantallas y API

| Ruta frontend | Función | API principal |
| --- | --- | --- |
| `/` | Inicio y buscador | `GET alojamientos/` |
| `/alojamientos` | Filtros y paginación | `GET alojamientos/?ciudad=&desde=&hasta=&huespedes=` |
| `/alojamientos/:id` | Galería, servicios, reglas, favoritos y reseñas | `GET alojamientos/{id}/`, `GET resenas/`, `GET/POST/DELETE favorito/` |
| `/reservar/:id` | Disponibilidad y total verificados | `GET alojamientos/{id}/disponibilidad/`, `POST reservas/` |
| `/confirmacion/:id` | Resultado persistido de la solicitud | `GET reservas/{id}/` |
| `/ingresar`, `/registro` | Autenticación | `auth/csrf/`, `auth/ingresar/`, `auth/registro/` |
| `/reservas` | Reservas propias o recibidas según rol | `GET reservas/`, acciones `estado/` y `cancelar/` |
| `/favoritos` | Alojamientos guardados | `GET cuenta/favoritos/` |
| `/panel` | Indicadores del anfitrión o administrador | `GET cuenta/panel/` |
| `/gestion/alojamientos` | Listado de gestión | `GET alojamientos/?mios=1` |
| `/gestion/alojamientos/nuevo` | Publicación por anfitrión | `POST alojamientos/` |
| `/gestion/alojamientos/:id` | Edición y fotografías | `PATCH alojamientos/{id}/`, acciones `fotos/` |
| `/usuarios` | Consulta administrativa de cuentas | `GET cuenta/usuarios/` |
| `/notificaciones` | Avisos propios y lectura | `GET notificaciones/`, `POST notificaciones/{id}/leer/` |
| `/asistente` | Asistente del backend con identidad comprobada | `POST asistente/` |
| `/ayuda` | Manual breve dentro del sistema | Contenido estático |

Las rutas de API de la tabla son relativas a `/api/v1/`. Los endpoints sugeridos en los documentos se adaptaron al dominio existente. No se creó un servicio ficticio de destinos: las ciudades de inicio son accesos directos al filtro real y pueden devolver un listado vacío.

## Estados y accesibilidad

Se implementan estados de carga, error con reintento, listas vacías y confirmación de operaciones. Los botones se bloquean durante los envíos. Cambiar fechas o cantidad de huéspedes invalida la cotización que permitía reservar. La confirmación de una solicitud no se confunde con la aceptación del anfitrión.

Se usan etiquetas asociadas, errores con `aria-describedby`, `aria-invalid`, regiones de estado y alerta, un enlace para saltar al contenido, indicadores textuales de estado y foco visible. La galería permite elegir fotos con botones. Las tablas permiten desplazamiento horizontal. Se respeta `prefers-reduced-motion`.

Los puntos de adaptación principales son 640, 900 y 1100 px. Hay filtros, menú y formularios adaptados a pantallas pequeñas. La familia tipográfica es Inter si está instalada, con alternativas del sistema; no se depende de Google Fonts ni de imágenes externas. La ilustración de portada es decorativa; las fotos de alojamientos provienen del anfitrión. No se presentan fotografías genéricas como si pertenecieran a una propiedad.

Estos controles no equivalen a certificar WCAG. Quedan por ejecutar la inspección visual en navegador real, un recorrido completo con teclado, axe y Lighthouse sobre cada ruta.

## Uso por rol

**Huésped:** crear cuenta o ingresar, buscar un alojamiento, consultar las fechas, aceptar las reglas y solicitar la reserva. Ver el resultado en Mis reservas. Cancelar reservas pendientes o confirmadas, guardar favoritos y publicar una reseña después de una estadía completada.

**Anfitrión:** ingresar a Mi panel, crear el alojamiento y guardar. En la pantalla de edición, seleccionar hasta cinco fotos y pulsar Publicar fotos. Elegir portada si corresponde. Revisar reservas para confirmar o rechazar; registrar entrada y completar la estadía en las fechas correspondientes. Pausar una publicación conserva su historial.

**Administrador:** consultar métricas globales, alojamientos, reservas y usuarios. Editar publicaciones y gestionar estados de reservas. La administración avanzada de usuarios y roles permanece en Django Admin y requiere su propia sesión. El registro público no permite seleccionar el rol administrador.

El asistente está disponible en `/asistente` para cuentas autenticadas. Solo una cuenta de huésped puede crear reservas por chat. La confirmación firmada vence en quince minutos y está vinculada al usuario; un `user_id` enviado por el navegador no cambia la identidad.

## Alcance que permanece fuera de esta entrega

No hay pasarela de pago, reembolsos bancarios, mensajería externa, verificación documental de identidad ni envío de correo para recuperación de contraseñas. No se inventan impuestos ni tarifas que no existan en el backend. Los datos del titular proceden de su cuenta y no se recopilan solicitudes especiales que el sistema no almacene. Las modificaciones a permisos avanzados continúan en Django Admin. No se publicó una instancia en Vercel o Render ni se modificaron tableros externos.
