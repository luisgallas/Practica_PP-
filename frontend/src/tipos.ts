export type Rol = 'admin' | 'anfitrion' | 'huesped'
export interface Usuario { id: number; username: string; first_name: string; last_name?: string; email?: string; telefono?: string; rol: Rol }
export interface Servicio { id: number; nombre: string }
export interface Foto { id: number; url: string; descripcion: string; es_portada: boolean }
export interface Alojamiento { id: number; titulo: string; descripcion: string; calle: string; ubicacion: string; tipo_alojamiento: string; capacidad_maxima_huespedes: number; precio_noche: string; precio_fin_semana: string; tarifa_limpieza: string; estado: string; permite_mascotas: boolean; permite_fumar: boolean; permite_fiestas: boolean; politica_cancelacion: string; anfitrion: Usuario; amenities: Servicio[]; fotos: Foto[]; puntuacion: number | null; cantidad_resenas: number }
export interface Pagina<T> { count: number; next: string | null; previous: string | null; results: T[] }
export interface Reserva { id: number; propiedad: Alojamiento; huesped: Usuario; fecha_inicio: string; fecha_fin: string; cantidad_huespedes: number; estado: string; precio_total: string; monto_reembolso: string; tiene_resena: boolean }
export interface Resena { id: number; usuario: Usuario; calificacion: number; comentario: string; fecha: string }
export interface Notificacion { id: number; mensaje: string; estado: string; fecha: string }
export interface Cotizacion { disponible: boolean; noches: number; total: string; limpieza: string }
export interface RespuestaChat { reply: string; accion_firmada?: string; intent: string }
