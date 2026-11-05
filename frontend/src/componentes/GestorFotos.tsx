import { useEffect, useState, type ChangeEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ImagePlus, Star, Trash2, X } from 'lucide-react'
import type { Foto } from '../tipos'
import { api, mensajeError } from '../servicios/api'
import { Aviso, Boton } from './Base'

export function validarFotos(archivos: File[], existentes: number) {
  if (existentes + archivos.length > 5) return 'Podés publicar hasta 5 fotos por alojamiento.'
  if (archivos.some(archivo => archivo.size > 5 * 1024 * 1024)) return 'Cada foto debe pesar como máximo 5 MB.'
  if (archivos.some(archivo => !['image/jpeg', 'image/png', 'image/webp'].includes(archivo.type))) return 'Seleccioná fotos JPEG, PNG o WebP.'
  return ''
}
export default function GestorFotos({ id, fotos }: { id: number; fotos: Foto[] }) {
  const [archivos, fijarArchivos] = useState<File[]>([]); const [vistas, fijarVistas] = useState<string[]>([]); const [error, fijarError] = useState(''); const [mensaje, fijarMensaje] = useState('')
  const consultas = useQueryClient()
  useEffect(() => { const urls = archivos.map(archivo => URL.createObjectURL(archivo)); fijarVistas(urls); return () => urls.forEach(url => URL.revokeObjectURL(url)) }, [archivos])
  const actualizar = () => { consultas.invalidateQueries({ queryKey: ['editar-alojamiento', String(id)] }); consultas.invalidateQueries({ queryKey: ['alojamiento', String(id)] }); consultas.invalidateQueries({ queryKey: ['gestion'] }); consultas.invalidateQueries({ queryKey: ['alojamientos'] }) }
  const cargar = useMutation({ mutationFn: async () => { const datos = new FormData(); archivos.forEach(archivo => datos.append('fotos', archivo)); return api.post(`alojamientos/${id}/fotos/`, datos, { timeout: 90000 }) }, onSuccess: () => { fijarArchivos([]); fijarMensaje('Fotos publicadas correctamente.'); actualizar() } })
  const eliminar = useMutation({ mutationFn: (foto: number) => api.delete(`alojamientos/${id}/fotos/${foto}/`), onSuccess: actualizar })
  const portada = useMutation({ mutationFn: (foto: number) => api.patch(`alojamientos/${id}/fotos/${foto}/portada/`), onSuccess: actualizar })
  const ocupado = cargar.isPending || eliminar.isPending || portada.isPending
  function seleccionar(evento: ChangeEvent<HTMLInputElement>) { const seleccion = [...archivos, ...Array.from(evento.target.files || [])]; const fallo = validarFotos(seleccion, fotos.length); fijarError(fallo); fijarMensaje(''); if (!fallo) fijarArchivos(seleccion); evento.target.value = '' }
  return <section className="panel gestor-fotos"><div className="titulo-seccion"><div><h2>Las fotos de tu espacio</h2><p>Hasta 5 imágenes. JPEG, PNG o WebP, máximo 5 MB por foto.</p></div><strong>{fotos.length + archivos.length} / 5</strong></div>{mensaje && <Aviso tipo="exito">{mensaje}</Aviso>}{error && <Aviso tipo="error">{error}</Aviso>}{[cargar, eliminar, portada].filter(operacion => operacion.isError).map((operacion, indice) => <Aviso key={indice} tipo="error">{mensajeError(operacion.error)}</Aviso>)}<div className="fotos-gestion">{fotos.map(foto => <div className="foto-gestion" key={foto.id}><img src={foto.url} alt={foto.descripcion || 'Foto del alojamiento'}/><div><Boton variante="contorno" disabled={ocupado || foto.es_portada} onClick={() => portada.mutate(foto.id)} aria-label={foto.es_portada ? 'Foto de portada' : 'Usar como portada'}><Star size={16}/>{foto.es_portada ? 'Portada' : 'Elegir'}</Boton><Boton variante="peligro" disabled={ocupado} onClick={() => eliminar.mutate(foto.id)} aria-label="Eliminar foto"><Trash2 size={16}/></Boton></div></div>)}{vistas.map((vista, indice) => <div className="foto-gestion" key={vista}><img src={vista} alt={`Vista previa: ${archivos[indice]?.name}`}/><div><span>Sin publicar</span><Boton variante="contorno" disabled={ocupado} onClick={() => fijarArchivos(archivos.filter((_, posicion) => posicion !== indice))} aria-label="Quitar foto seleccionada"><X size={16}/></Boton></div></div>)}</div>{fotos.length + archivos.length < 5 && <div className="carga-fotos"><ImagePlus size={28}/><label htmlFor="fotos">Seleccioná las fotos de tu alojamiento</label><input id="fotos" type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={seleccionar} disabled={ocupado}/><small>La primera foto será la portada. Podés cambiarla después.</small></div>}{!!archivos.length && <Boton ocupado={cargar.isPending} disabled={eliminar.isPending || portada.isPending} onClick={() => cargar.mutate()}>Publicar {archivos.length} {archivos.length === 1 ? 'foto' : 'fotos'}</Boton>}</section>
}
