import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import Asistente from '../paginas/Asistente'
import { api } from '../servicios/api'

vi.mock('../contextos/Sesion', () => ({ usarSesion: () => ({ usuario: { id: 1, rol: 'huesped' } }) }))
vi.mock('../servicios/api', () => ({ api: { post: vi.fn() }, mensajeError: () => 'Error de conexión' }))
function mostrar() { render(<QueryClientProvider client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}><MemoryRouter><Asistente/></MemoryRouter></QueryClientProvider>) }
beforeEach(() => vi.clearAllMocks())
describe('Reserva guiada por chat', () => {
  it('conserva el contexto entre mensajes y confirma con la acción firmada', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { reply: '¿Qué fechas?', contexto_firmado: 'contexto-1' } })
      .mockResolvedValueOnce({ data: { reply: 'Revisá el total y las condiciones.', contexto_firmado: 'contexto-2', accion_firmada: 'accion-segura' } })
      .mockResolvedValueOnce({ data: { reply: 'Solicitud creada.', intent: 'create_reservation_confirmed', data: { id: 42 } } })
    mostrar()
    await userEvent.click(screen.getByRole('button', { name: 'Buscar alojamiento' }))
    await screen.findByText('¿Qué fechas?')
    await userEvent.type(screen.getByLabelText('Mensaje para el asistente'), '20/12/2027 al 22/12/2027')
    await userEvent.click(screen.getByRole('button', { name: /Enviar/ }))
    await screen.findByText('Revisá el total y las condiciones.')
    expect(api.post).toHaveBeenNthCalledWith(2, 'asistente/', expect.objectContaining({ contexto_firmado: 'contexto-1' }))
    expect(api.post).toHaveBeenCalledTimes(2)
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar solicitud y condiciones' }))
    expect(api.post).toHaveBeenLastCalledWith('asistente/', expect.objectContaining({ confirm: true, accion_firmada: 'accion-segura', contexto_firmado: 'contexto-2' }))
    expect(await screen.findByRole('link', { name: 'Ver solicitud #42' })).toHaveAttribute('href', '/confirmacion/42')
    expect(screen.queryByRole('button', { name: 'Confirmar solicitud y condiciones' })).not.toBeInTheDocument()
  })
  it('descarta la búsqueda sin confirmar y permite empezar otra conversación', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { reply: 'Resumen.', contexto_firmado: 'contexto', accion_firmada: 'accion' } })
      .mockResolvedValueOnce({ data: { reply: 'Descartado.', contexto_firmado: 'vacio' } })
    mostrar()
    await userEvent.click(screen.getByRole('button', { name: 'Buscar alojamiento' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Descartar' }))
    await screen.findByText('Descartado.')
    expect(api.post).toHaveBeenLastCalledWith('asistente/', expect.objectContaining({ message: 'descartar', confirm: false }))
    await userEvent.click(screen.getByRole('button', { name: 'Nueva conversación' }))
    await waitFor(() => expect(screen.queryByText('Descartado.')).not.toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Buscar alojamiento' })).toBeEnabled()
  })
})
