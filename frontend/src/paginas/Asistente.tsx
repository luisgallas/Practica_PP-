import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { BotMessageSquare, Send } from 'lucide-react'
import { api, mensajeError } from '../servicios/api'
import { usarSesion } from '../contextos/Sesion'
import type { RespuestaChat } from '../tipos'
import { Aviso, Boton } from '../componentes/Base'

type Turno = { texto: string; autor: string; opciones?: { id: number; titulo: string }[]; reserva?: number }
export default function Asistente() {
  const { usuario } = usarSesion()
  const consultas = useQueryClient()
  const [mensaje, fijarMensaje] = useState('')
  const [conversacion, fijarConversacion] = useState<Turno[]>([])
  const [accion, fijarAccion] = useState('')
  const [contexto, fijarContexto] = useState('')
  const registro = useRef<HTMLDivElement>(null)
  const enviar = useMutation({
    mutationFn: async (datos: { message: string; confirm?: boolean; accion_firmada?: string; contexto_firmado?: string }) => (await api.post<RespuestaChat>('asistente/', datos)).data,
    onSuccess: resultado => {
      const reserva = resultado.intent === 'create_reservation_confirmed' ? resultado.data?.id : undefined
      fijarConversacion(anterior => [...anterior, { texto: resultado.reply, autor: 'asistente', opciones: resultado.opciones, reserva }])
      fijarAccion(resultado.accion_firmada || '')
      fijarContexto(resultado.contexto_firmado || '')
      if (reserva) {
        for (const clave of ['reservas', 'alojamientos', 'panel', 'notificaciones', 'cotizacion']) consultas.invalidateQueries({ queryKey: [clave] })
      }
    },
  })
  useEffect(() => { if (registro.current) registro.current.scrollTop = registro.current.scrollHeight }, [conversacion, enviar.isPending])
  function consultar(texto: string, confirmar = false) {
    if (enviar.isPending) return
    fijarConversacion(anterior => [...anterior, { texto, autor: 'vos' }])
    fijarMensaje('')
    enviar.mutate({ message: texto, contexto_firmado: contexto, accion_firmada: accion || undefined, confirm: confirmar })
    if (!confirmar && !/^(sí|si|confirmo|confirmar|dale|si confirmo|sí confirmo|si, confirmo|sí, confirmo)$/i.test(texto)) fijarAccion('')
  }
  function reiniciar() { fijarConversacion([]); fijarContexto(''); fijarAccion(''); fijarMensaje(''); enviar.reset() }
  const huesped = usuario?.rol === 'huesped'
  return <section className="contenedor seccion chat"><p className="sobrelinea">{huesped ? 'UNA MANO PARA TU VIAJE' : 'UNA MANO PARA TU GESTIÓN'}</p><h1><BotMessageSquare/> Asistente de Hospeda PY</h1><p>{huesped ? 'Te ayudo a elegir alojamiento y preparar tu reserva paso a paso. Antes de crearla, te pediré confirmación.' : usuario?.rol === 'admin' ? 'Consultá reservas del sistema por ciudad y estado, o buscá disponibilidad.' : 'Consultá las reservas de tus alojamientos por ciudad y estado, o buscá disponibilidad.'}</p><div className="panel"><Boton variante="contorno" disabled={enviar.isPending} onClick={reiniciar}>Nueva conversación</Boton><div ref={registro} className="mensajes-chat" role="log" aria-live="polite">{!conversacion.length && <div className="estado-vacio"><BotMessageSquare size={40}/><h2>¿En qué te ayudo?</h2><p>{huesped ? 'Decime dónde querés alojarte. Te iré preguntando las fechas y la cantidad de huéspedes.' : 'Probá consultar tus reservas pendientes o preguntar cuántas hay en una ciudad.'}</p><div className="acciones-reserva"><Boton variante="contorno" ocupado={enviar.isPending} onClick={() => consultar(huesped ? 'Quiero reservar un alojamiento' : 'Mostrar reservas pendientes')}>{huesped ? 'Buscar alojamiento' : 'Ver reservas pendientes'}</Boton><Boton variante="contorno" disabled={enviar.isPending} onClick={() => consultar('Mostrar mis reservas')}>Consultar reservas</Boton></div></div>}{conversacion.map((turno, indice) => <div key={indice} className={`mensaje-chat mensaje-${turno.autor}`}><strong>{turno.autor === 'vos' ? 'Vos' : 'Hospeda PY'}</strong><p style={{ whiteSpace: 'pre-line' }}>{turno.texto}</p>{turno.opciones?.map((opcion, posicion) => <div key={opcion.id} className="acciones-reserva"><Boton variante="contorno" disabled={enviar.isPending || indice !== conversacion.length - 1} onClick={() => consultar(String(posicion + 1))}>Elegir {posicion + 1}</Boton><Link to={`/alojamientos/${opcion.id}`} target="_blank" rel="noopener noreferrer">Ver {opcion.titulo}</Link></div>)}{turno.reserva && <Link className="boton boton-primario" to={`/confirmacion/${turno.reserva}`}>Ver solicitud #{turno.reserva}</Link>}</div>)}{enviar.isPending && <p role="status">Consultando el sistema…</p>}</div>{enviar.isError && <Aviso tipo="error">{mensajeError(enviar.error)} Podés corregir tu mensaje o iniciar una nueva conversación.</Aviso>}{accion && <div className="acciones-reserva"><Boton ocupado={enviar.isPending} onClick={() => consultar('confirmo', true)}>Confirmar solicitud y condiciones</Boton><Boton variante="contorno" disabled={enviar.isPending} onClick={() => consultar('descartar')}>Descartar</Boton></div>}<form className="formulario-chat" onSubmit={evento => { evento.preventDefault(); if (mensaje.trim()) consultar(mensaje.trim()) }}><label className="sr-only" htmlFor="mensaje">Mensaje para el asistente</label><input id="mensaje" value={mensaje} onChange={evento => fijarMensaje(evento.target.value)} maxLength={2000} placeholder={huesped ? 'Quiero alojarme en Villarrica…' : '¿Cuántas reservas tengo en Villarrica?'} required disabled={enviar.isPending}/><Boton type="submit" ocupado={enviar.isPending} disabled={!mensaje.trim()}><Send size={18}/> Enviar</Boton></form></div></section>
}
