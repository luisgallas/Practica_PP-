import { Link, useLocation } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { usarSesion } from '../contextos/Sesion'
import type { Rol } from '../tipos'

export function destinoVolver(ruta: string, rol?: Rol) {
  if (ruta === '/') return null
  if (ruta === '/ingresar' || ruta === '/registro' || ruta === '/panel' || ruta === '/alojamientos') return { ruta: '/', texto: 'Volver al inicio' }
  if (ruta.startsWith('/gestion/alojamientos/')) return { ruta: '/gestion/alojamientos', texto: 'Volver a alojamientos' }
  const reserva = ruta.match(/^\/reservar\/(\d+)\/?$/)
  if (reserva) return { ruta: `/alojamientos/${reserva[1]}`, texto: 'Volver al alojamiento' }
  if (ruta.startsWith('/alojamientos/')) return { ruta: '/alojamientos', texto: 'Volver a explorar' }
  if (ruta.startsWith('/confirmacion/')) return { ruta: '/reservas', texto: 'Volver a mis reservas' }
  return rol === 'admin' || rol === 'anfitrion' ? { ruta: '/panel', texto: 'Volver a mi panel' } : { ruta: '/alojamientos', texto: 'Volver a explorar' }
}

export default function Volver() {
  const { pathname } = useLocation()
  const { usuario } = usarSesion()
  const destino = destinoVolver(pathname, usuario?.rol)
  if (!destino) return null
  return <nav className="contenedor navegacion-volver" aria-label="Volver a la pantalla anterior"><Link className="boton boton-contorno" to={destino.ruta}><ArrowLeft size={17}/>{destino.texto}</Link></nav>
}
