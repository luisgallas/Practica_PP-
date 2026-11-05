import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { Boton, Aviso } from './Base'
import { hoy } from '../servicios/formato'

export default function Buscador() {
  const navegar = useNavigate(); const [error, fijarError] = useState('')
  function buscar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); const formulario = new FormData(evento.currentTarget)
    const desde = String(formulario.get('desde') || ''); const hasta = String(formulario.get('hasta') || '')
    if ((desde && !hasta) || (!desde && hasta) || (desde && (desde < hoy() || hasta <= desde))) { fijarError('Elegí entrada y salida válidas. La salida debe ser posterior a la entrada.'); return }
    const parametros = new URLSearchParams(); formulario.forEach((valor, clave) => { if (valor) parametros.set(clave, String(valor)) }); navegar(`/alojamientos?${parametros}`)
  }
  return <div className="buscador-contenedor"><form className="buscador" onSubmit={buscar}><div><label htmlFor="destino">¿A dónde vamos?</label><input id="destino" name="ciudad" placeholder="Ciudad o destino" maxLength={100}/></div><div><label htmlFor="entrada">Entrada</label><input type="date" id="entrada" name="desde" min={hoy()}/></div><div><label htmlFor="salida">Salida</label><input type="date" id="salida" name="hasta" min={hoy()}/></div><div className="campo-huespedes"><label htmlFor="huespedes">Huéspedes</label><select id="huespedes" name="huespedes">{[1, 2, 3, 4, 5, 6, 8, 10].map(numero => <option key={numero} value={numero}>{numero} {numero === 1 ? 'huésped' : 'huéspedes'}</option>)}</select></div><Boton type="submit"><Search size={20}/> Buscar</Boton></form>{error && <Aviso tipo="error">{error}</Aviso>}</div>
}
