import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, mensajeError } from '../servicios/api'
import { fecha } from '../servicios/formato'
import type { Alojamiento, Notificacion, Pagina, Usuario } from '../tipos'
import { Aviso, Boton, Cargando, ErrorConsulta, Insignia, Paginacion, TablaDatos, Vacio } from '../componentes/Base'
import TarjetaAlojamiento from '../componentes/TarjetaAlojamiento'

export function Favoritos() {
  const [pagina, fijarPagina] = useState(1)
  const consulta = useQuery({ queryKey: ['favoritos', pagina], queryFn: async () => (await api.get<Pagina<Alojamiento>>(`cuenta/favoritos/?page=${pagina}`)).data })
  return <section className="contenedor seccion"><p className="sobrelinea">PARA TU PRÓXIMO VIAJE</p><h1>Tus lugares guardados</h1><p>Esos espacios a los que querés volver.</p>{consulta.isPending ? <Cargando/> : consulta.isError ? <ErrorConsulta error={consulta.error} reintentar={() => consulta.refetch()}/> : <>{consulta.data.results.length ? <div className="rejilla-tarjetas">{consulta.data.results.map(alojamiento => <TarjetaAlojamiento key={alojamiento.id} alojamiento={alojamiento}/>)}</div> : <Vacio titulo="Tu lista de deseos empieza acá"><p>Guardá un alojamiento desde su página de detalle.</p><Link className="boton boton-primario" to="/alojamientos">Encontrar un lugar</Link></Vacio>}<Paginacion pagina={pagina} total={consulta.data.count} siguiente={!!consulta.data.next} cambiar={fijarPagina}/></>}</section>
}
export function Notificaciones() {
  const [pagina, fijarPagina] = useState(1); const consultas = useQueryClient()
  const consulta = useQuery({ queryKey: ['notificaciones', pagina], queryFn: async () => (await api.get<Pagina<Notificacion>>(`notificaciones/?page=${pagina}`)).data })
  const leer = useMutation({ mutationFn: (id: number) => api.post(`notificaciones/${id}/leer/`), onSuccess: () => consultas.invalidateQueries({ queryKey: ['notificaciones'] }) })
  return <section className="contenedor seccion"><p className="sobrelinea">AL DÍA CON TU ESTADÍA</p><h1>Notificaciones</h1>{leer.isError && <Aviso tipo="error">{mensajeError(leer.error)}</Aviso>}{consulta.isPending ? <Cargando/> : consulta.isError ? <ErrorConsulta error={consulta.error} reintentar={() => consulta.refetch()}/> : <>{consulta.data.results.length ? <div className="lista-notificaciones">{consulta.data.results.map(aviso => <article key={aviso.id} className="panel notificacion"><div><Insignia estado={aviso.estado}/><p>{aviso.mensaje}</p><small>{fecha(aviso.fecha)}</small></div>{aviso.estado !== 'leida' && <Boton variante="contorno" disabled={leer.isPending} onClick={() => leer.mutate(aviso.id)}>Marcar como leída</Boton>}</article>)}</div> : <Vacio titulo="Estás al día"><p>Acá recibirás novedades sobre tus reservas.</p></Vacio>}<Paginacion pagina={pagina} total={consulta.data.count} siguiente={!!consulta.data.next} cambiar={fijarPagina}/></>}</section>
}
export function Usuarios() {
  const [pagina, fijarPagina] = useState(1)
  const consulta = useQuery({ queryKey: ['usuarios', pagina], queryFn: async () => (await api.get<Pagina<Usuario>>(`cuenta/usuarios/?page=${pagina}`)).data })
  return <section className="contenedor seccion"><p className="sobrelinea">ADMINISTRACIÓN</p><h1>Usuarios del sistema</h1><p>Los cambios de roles y permisos se realizan en la <a href={`${(import.meta.env.VITE_API_URL || '/api/v1/').replace(/\/api\/v1\/?$/, '')}/admin/presupuesto/usuario/`}>administración de Django</a>.</p>{consulta.isPending ? <Cargando/> : consulta.isError ? <ErrorConsulta error={consulta.error} reintentar={() => consulta.refetch()}/> : <><TablaDatos columnas={['Usuario', 'Nombre', 'Correo', 'Rol']} vacia={!consulta.data.results.length}>{consulta.data.results.map(usuario => <tr key={usuario.id}><td>{usuario.username}</td><td>{usuario.first_name} {usuario.last_name}</td><td>{usuario.email || 'Sin correo'}</td><td><Insignia estado={usuario.rol}/></td></tr>)}</TablaDatos><Paginacion pagina={pagina} total={consulta.data.count} siguiente={!!consulta.data.next} cambiar={fijarPagina}/></>}</section>
}
