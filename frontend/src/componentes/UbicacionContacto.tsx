import { MapPin, Phone } from 'lucide-react'
import type { Alojamiento } from '../tipos'

export function esEnlaceMaps(valor: string) {
  try {
    const url = new URL(valor)
    return url.protocol === 'https:' && !url.username && !url.password && !url.port && (
      url.hostname === 'maps.app.goo.gl' ||
      (url.hostname === 'goo.gl' && url.pathname.startsWith('/maps/')) ||
      url.hostname === 'maps.google.com' ||
      (['google.com', 'www.google.com'].includes(url.hostname) && (url.pathname === '/maps' || url.pathname.startsWith('/maps/'))))
  } catch { return false }
}

export default function UbicacionContacto({ alojamiento }: { alojamiento: Alojamiento }) {
  const enlace = alojamiento.google_maps_url && esEnlaceMaps(alojamiento.google_maps_url) ? alojamiento.google_maps_url : ''
  const direccion = [alojamiento.calle, alojamiento.ubicacion, 'Paraguay'].filter(Boolean).join(', ')
  const busqueda = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(direccion)}`
  return <section className="ubicacion-contacto" aria-label="Ubicación y contacto"><h3>Ubicación y contacto</h3><p><MapPin size={16}/> {direccion}</p><a className="boton boton-contorno" href={enlace || busqueda} target="_blank" rel="noopener noreferrer"><MapPin size={17}/>{enlace ? 'Ver ubicación en Google Maps' : 'Buscar dirección en Google Maps'}</a>{!enlace && <p className="nota-reserva">El anfitrión todavía no compartió un punto exacto. La búsqueda usa la dirección publicada.</p>}{alojamiento.telefono_contacto ? <p><a className="enlace-telefono" href={`tel:${alojamiento.telefono_contacto.replace(/[^+0-9]/g, '')}`}><Phone size={17}/> {alojamiento.telefono_contacto}</a></p> : <p className="nota-reserva">El anfitrión todavía no añadió un teléfono de contacto.</p>}</section>
}
