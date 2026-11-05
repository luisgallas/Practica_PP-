import { Link } from 'react-router-dom'
import { ArrowUpRight, MapPin, Star, Users } from 'lucide-react'
import type { Alojamiento } from '../tipos'
import { guaranies, tipos } from '../servicios/formato'

export default function TarjetaAlojamiento({ alojamiento }: { alojamiento: Alojamiento }) {
  return <article className="tarjeta-alojamiento"><Link to={`/alojamientos/${alojamiento.id}`} className="imagen-tarjeta" aria-label={`Ver ${alojamiento.titulo}`}><img src={alojamiento.fotos[0]?.url || '/sin-foto.svg'} alt={alojamiento.fotos.length ? alojamiento.titulo : 'Alojamiento sin fotografías publicadas'} loading="lazy" width="600" height="420"/><span className="etiqueta-tipo">{tipos[alojamiento.tipo_alojamiento] || alojamiento.tipo_alojamiento}</span><span className="flecha-tarjeta"><ArrowUpRight size={20}/></span></Link><div className="tarjeta-contenido"><div className="linea-entre"><span className="ubicacion"><MapPin size={14}/>{alojamiento.ubicacion}</span><span className="puntaje"><Star size={14}/>{alojamiento.puntuacion ? Number(alojamiento.puntuacion).toFixed(1) : 'Nuevo'}</span></div><h3><Link to={`/alojamientos/${alojamiento.id}`}>{alojamiento.titulo}</Link></h3><p className="capacidad"><Users size={15}/> Hasta {alojamiento.capacidad_maxima_huespedes} huéspedes</p><div className="precio-tarjeta"><strong>{guaranies(alojamiento.precio_noche)}</strong><span> / noche</span></div></div></article>
}
