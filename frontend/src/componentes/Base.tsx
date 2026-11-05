import { forwardRef, useId, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode } from 'react'
import { AlertCircle, ArrowLeft, ArrowRight, LoaderCircle, SearchX } from 'lucide-react'
import { mensajeError } from '../servicios/api'

export function Boton({ children, variante = 'primario', ocupado = false, className = '', disabled, ...resto }: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: 'primario' | 'secundario' | 'peligro' | 'contorno'; ocupado?: boolean }) {
  return <button className={`boton boton-${variante} ${className}`} disabled={disabled || ocupado} aria-busy={ocupado} {...resto}>{ocupado ? <><LoaderCircle className="girar" size={18}/> Procesando…</> : children}</button>
}
export const Campo = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & { etiqueta: string; error?: string; ayuda?: string }>(function Campo({ etiqueta, error, ayuda, id, ...resto }, referencia) {
  const generado = useId(); const identificador = id || generado
  return <div className="campo"><label htmlFor={identificador}>{etiqueta}</label><input id={identificador} ref={referencia} aria-invalid={!!error} aria-describedby={error || ayuda ? `${identificador}-ayuda` : undefined} {...resto}/>{(error || ayuda) && <small id={`${identificador}-ayuda`} className={error ? 'texto-error' : ''}>{error || ayuda}</small>}</div>
})
export function Aviso({ children, tipo = 'informacion' }: { children: ReactNode; tipo?: 'error' | 'exito' | 'informacion' }) { return <div className={`aviso aviso-${tipo}`} role={tipo === 'error' ? 'alert' : 'status'}><AlertCircle size={19}/><div>{children}</div></div> }
export function Cargando({ cantidad = 3 }: { cantidad?: number }) { return <div role="status" aria-label="Cargando contenido"><span className="sr-only">Cargando…</span><div className="rejilla-tarjetas">{Array.from({ length: cantidad }, (_, indice) => <div key={indice} className="esqueleto"/>)}</div></div> }
export function ErrorConsulta({ error, reintentar }: { error: unknown; reintentar: () => void }) { return <div className="estado-vacio"><AlertCircle size={36}/><h2>No pudimos cargar el contenido</h2><p>{mensajeError(error)}</p><Boton variante="contorno" onClick={reintentar}>Reintentar</Boton></div> }
export function Vacio({ titulo = 'No encontramos alojamientos', children }: { titulo?: string; children?: ReactNode }) { return <div className="estado-vacio"><SearchX size={36}/><h2>{titulo}</h2>{children}</div> }
export function Paginacion({ pagina, total, siguiente, cambiar }: { pagina: number; total: number; siguiente: boolean; cambiar: (pagina: number) => void }) {
  if (!total) return null
  return <nav className="paginacion" aria-label="Páginas de resultados"><Boton variante="contorno" disabled={pagina <= 1} onClick={() => cambiar(pagina - 1)}><ArrowLeft size={16}/> Anterior</Boton><span>Página {pagina} · {total} resultados</span><Boton variante="contorno" disabled={!siguiente} onClick={() => cambiar(pagina + 1)}>Siguiente <ArrowRight size={16}/></Boton></nav>
}
export function Insignia({ estado }: { estado: string }) { return <span className={`insignia estado-${estado}`}>{estado.replaceAll('_', ' ')}</span> }
export function TablaDatos({ columnas, children, vacia = false }: { columnas: string[]; children: ReactNode; vacia?: boolean }) { return <div className="tabla-contenedor" tabIndex={0} role="region" aria-label="Tabla de datos"><table><thead><tr>{columnas.map(columna => <th key={columna} scope="col">{columna}</th>)}</tr></thead><tbody>{vacia ? <tr><td colSpan={columnas.length}>Todavía no hay registros.</td></tr> : children}</tbody></table></div> }
