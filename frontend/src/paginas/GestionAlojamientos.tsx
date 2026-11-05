import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { usarSesion } from '../contextos/Sesion'
import { api } from '../servicios/api'
import { guaranies } from '../servicios/formato'
import type { Alojamiento, Pagina } from '../tipos'
import { Cargando, ErrorConsulta, Insignia, Paginacion, TablaDatos } from '../componentes/Base'
export default function GestionAlojamientos() {
  const [pagina, fijarPagina] = useState(1); const { usuario } = usarSesion()
  const consulta = useQuery({ queryKey: ['gestion', pagina], queryFn: async () => (await api.get<Pagina<Alojamiento>>(`alojamientos/?mios=1&page=${pagina}`)).data })
  return <section className="contenedor seccion"><div className="titulo-seccion"><div><p className="sobrelinea">TUS ESPACIOS</p><h1>{usuario?.rol === 'admin' ? 'Alojamientos del sistema' : 'Mis alojamientos'}</h1><p>Gestioná tus publicaciones, precios y fotografías.</p></div>{usuario?.rol === 'anfitrion' && <Link className="boton boton-primario" to="/gestion/alojamientos/nuevo"><Plus size={18}/> Nuevo alojamiento</Link>}</div>{consulta.isPending ? <Cargando/> : consulta.isError ? <ErrorConsulta error={consulta.error} reintentar={() => consulta.refetch()}/> : <><TablaDatos columnas={['Alojamiento', 'Estado', 'Precio / noche', 'Fotos', 'Gestión']} vacia={!consulta.data.results.length}>{consulta.data.results.map(alojamiento => <tr key={alojamiento.id}><td><div className="celda-alojamiento"><img src={alojamiento.fotos[0]?.url || '/sin-foto.svg'} alt="" width="64" height="52"/><div><strong>{alojamiento.titulo}</strong><small>{alojamiento.ubicacion}</small></div></div></td><td><Insignia estado={alojamiento.estado}/></td><td>{guaranies(alojamiento.precio_noche)}</td><td>{alojamiento.fotos.length} / 5</td><td><Link className="boton boton-contorno" to={`/gestion/alojamientos/${alojamiento.id}`}><Pencil size={16}/> Editar</Link></td></tr>)}</TablaDatos><Paginacion pagina={pagina} total={consulta.data.count} siguiente={!!consulta.data.next} cambiar={fijarPagina}/></>}</section>
}
