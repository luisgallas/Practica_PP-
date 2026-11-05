import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { api, ingresar, renovarAcceso, salir } from '../servicios/api'
import type { Usuario } from '../tipos'

const Contexto = createContext<{ usuario: Usuario | null; cargando: boolean; iniciar: (datos: { username: string; password: string }) => Promise<Usuario>; cerrar: () => Promise<void> } | null>(null)
export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [usuario, fijarUsuario] = useState<Usuario | null>(null)
  const [cargando, fijarCargando] = useState(true)
  const consultas = useQueryClient()
  useEffect(() => {
    let vigente = true
    renovarAcceso().then(() => api.get<Usuario>('cuenta/perfil/')).then(({ data }) => { if (vigente) fijarUsuario(data) }).catch(() => { /* Sin cookie válida, se mantiene la navegación pública. */ }).finally(() => { if (vigente) fijarCargando(false) })
    const vencida = () => { fijarUsuario(null); consultas.clear() }
    window.addEventListener('sesion-vencida', vencida)
    return () => { vigente = false; window.removeEventListener('sesion-vencida', vencida) }
  }, [consultas])
  async function iniciar(datos: { username: string; password: string }) { const persona = await ingresar(datos); consultas.clear(); fijarUsuario(persona); return persona }
  async function cerrar() { await salir(); consultas.clear(); fijarUsuario(null) }
  return <Contexto.Provider value={{ usuario, cargando, iniciar, cerrar }}>{children}</Contexto.Provider>
}
export function usarSesion() { const contexto = useContext(Contexto); if (!contexto) throw new Error('Falta el proveedor de sesión.'); return contexto }
