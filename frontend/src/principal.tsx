import { lazy, Suspense, type ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProveedorSesion, usarSesion } from './contextos/Sesion'
import Estructura from './componentes/Estructura'
import { Cargando } from './componentes/Base'
import type { Rol } from './tipos'
import './estilos.css'
const Inicio = lazy(() => import('./paginas/Inicio'))
const Alojamientos = lazy(() => import('./paginas/Alojamientos'))
const Detalle = lazy(() => import('./paginas/Detalle'))
const Autenticacion = lazy(() => import('./paginas/Autenticacion'))
const Reservar = lazy(() => import('./paginas/Reservar'))
const Confirmacion = lazy(() => import('./paginas/Reservar').then(modulo => ({ default: modulo.Confirmacion })))
const Reservas = lazy(() => import('./paginas/Reservas'))
const Panel = lazy(() => import('./paginas/Panel'))
const Gestion = lazy(() => import('./paginas/GestionAlojamientos'))
const Editor = lazy(() => import('./paginas/EditarAlojamiento'))
const Favoritos = lazy(() => import('./paginas/Cuenta').then(modulo => ({ default: modulo.Favoritos })))
const Notificaciones = lazy(() => import('./paginas/Cuenta').then(modulo => ({ default: modulo.Notificaciones })))
const Usuarios = lazy(() => import('./paginas/Cuenta').then(modulo => ({ default: modulo.Usuarios })))
const Asistente = lazy(() => import('./paginas/Asistente'))
const Ayuda = lazy(() => import('./paginas/Ayuda'))
function Protegida({ children, roles }: { children: ReactNode; roles?: Rol[] }) {
  const { usuario, cargando } = usarSesion(); const ubicacion = useLocation()
  if (cargando) return <Cargando/>
  if (!usuario) return <Navigate replace to={`/ingresar?siguiente=${encodeURIComponent(ubicacion.pathname + ubicacion.search)}`}/>
  if (roles && !roles.includes(usuario.rol)) return <section className="contenedor seccion"><h1>Esta sección corresponde a otro rol</h1><p>Tu cuenta no tiene permisos para acceder a esta pantalla.</p><Link to="/">Volver al inicio</Link></section>
  return children
}
const consultas = new QueryClient({ defaultOptions: { queries: { staleTime: 30000, retry: 1, refetchOnWindowFocus: false } } })
createRoot(document.getElementById('raiz')!).render(<QueryClientProvider client={consultas}><BrowserRouter><ProveedorSesion><Suspense fallback={<div className="contenedor seccion"><Cargando/></div>}><Routes><Route element={<Estructura/>}><Route index element={<Inicio/>}/><Route path="alojamientos" element={<Alojamientos/>}/><Route path="alojamientos/:id" element={<Detalle/>}/><Route path="reservar/:id" element={<Reservar/>}/><Route path="ingresar" element={<Autenticacion key="ingreso"/>}/><Route path="registro" element={<Autenticacion key="registro" registro/>}/><Route path="confirmacion/:id" element={<Protegida><Confirmacion/></Protegida>}/><Route path="reservas" element={<Protegida><Reservas/></Protegida>}/><Route path="panel" element={<Protegida roles={['admin', 'anfitrion']}><Panel/></Protegida>}/><Route path="gestion/alojamientos" element={<Protegida roles={['admin', 'anfitrion']}><Gestion/></Protegida>}/><Route path="gestion/alojamientos/nuevo" element={<Protegida roles={['anfitrion']}><Editor key="nuevo"/></Protegida>}/><Route path="gestion/alojamientos/:id" element={<Protegida roles={['admin', 'anfitrion']}><Editor key="edicion"/></Protegida>}/><Route path="favoritos" element={<Protegida roles={['huesped']}><Favoritos/></Protegida>}/><Route path="notificaciones" element={<Protegida><Notificaciones/></Protegida>}/><Route path="usuarios" element={<Protegida roles={['admin']}><Usuarios/></Protegida>}/><Route path="asistente" element={<Protegida><Asistente/></Protegida>}/><Route path="ayuda" element={<Ayuda/>}/><Route path="*" element={<section className="contenedor seccion"><h1>No encontramos esta página</h1><Link to="/">Volver al inicio</Link></section>}/></Route></Routes></Suspense></ProveedorSesion></BrowserRouter></QueryClientProvider>)
