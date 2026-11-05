import axios, { AxiosError } from 'axios'
import type { Usuario } from '../tipos'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api/v1/', withCredentials: true, timeout: 20000, paramsSerializer: { indexes: null } })
const sesion = axios.create({ baseURL: api.defaults.baseURL, withCredentials: true, timeout: 20000 })
let acceso: string | null = null
let csrf = ''
let renovacion: Promise<string> | null = null
let generacion = 0
export function limpiarAcceso() { acceso = null; generacion++ }
export async function obtenerCsrf() { csrf = (await sesion.get('auth/csrf/')).data.csrfToken; return csrf }
export async function renovarAcceso() {
  if (!renovacion) {
    const actual = generacion
    renovacion = (async () => {
      await obtenerCsrf()
      const respuesta = await sesion.post('auth/renovar/', {}, { headers: { 'X-CSRFToken': csrf } })
      if (actual !== generacion) throw new Error('La sesión cambió.')
      acceso = respuesta.data.access
      return acceso!
    })().finally(() => { renovacion = null })
  }
  return renovacion
}
api.interceptors.request.use(configuracion => {
  if (acceso) configuracion.headers.Authorization = `Bearer ${acceso}`
  return configuracion
})
api.interceptors.response.use(respuesta => respuesta, async (error: AxiosError) => {
  const configuracion = error.config as (NonNullable<typeof error.config> & { reintentado?: boolean }) | undefined
  if (error.response?.status !== 401 || !configuracion || configuracion.reintentado) throw error
  configuracion.reintentado = true
  try { await renovarAcceso(); return api(configuracion) }
  catch { limpiarAcceso(); window.dispatchEvent(new Event('sesion-vencida')); throw error }
})
export async function ingresar(datos: { username: string; password: string }): Promise<Usuario> {
  await obtenerCsrf()
  const respuesta = await sesion.post('auth/ingresar/', datos, { headers: { 'X-CSRFToken': csrf } })
  generacion++; acceso = respuesta.data.access; csrf = respuesta.data.csrfToken
  return respuesta.data.usuario
}
export async function registrar(datos: Record<string, unknown>) {
  await obtenerCsrf()
  return sesion.post('auth/registro/', datos, { headers: { 'X-CSRFToken': csrf } })
}
export async function salir() {
  await obtenerCsrf()
  await sesion.post('auth/salir/', {}, { headers: { 'X-CSRFToken': csrf } })
  limpiarAcceso()
}
export function mensajeError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) return 'No pudimos conectar con el servidor. Revisá tu conexión y volvé a intentar.'
    if (error.response.status === 429) return 'Realizaste muchas solicitudes. Esperá un minuto y volvé a intentar.'
    if (error.response.status >= 500) return 'El servidor no pudo completar la solicitud. Intentá nuevamente.'
    const datos = error.response.data
    if (typeof datos === 'string') return 'No pudimos completar la solicitud.'
    if (datos?.detail) return String(datos.detail)
    if (datos) return Object.entries(datos).map(([campo, valor]) => `${campo === 'non_field_errors' ? '' : campo + ': '}${Array.isArray(valor) ? valor.join(' ') : valor}`).join(' ')
  }
  return error instanceof Error ? error.message : 'Ocurrió un error. Volvé a intentar.'
}
