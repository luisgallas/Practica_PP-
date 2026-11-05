import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import usuario from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Reservar from '../paginas/Reservar'
import { api } from '../servicios/api'

vi.mock('../contextos/Sesion', () => ({ usarSesion: () => ({ usuario: { id: 1, username: 'prueba', first_name: 'Ana', rol: 'huesped' } }) }))
vi.mock('../servicios/api', () => ({ api: { get: vi.fn(), post: vi.fn() }, mensajeError: () => 'No se pudo completar la solicitud.' }))
const alojamiento = { id: 1, titulo: 'Casa de prueba', ubicacion: 'Villarrica', fotos: [], capacidad_maxima_huespedes: 4, politica_cancelacion: 'flexible' }
function mostrar() { return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><MemoryRouter initialEntries={['/reservar/1']}><Routes><Route path="/reservar/:id" element={<Reservar/>}/></Routes></MemoryRouter></QueryClientProvider>) }
beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(api.get).mockImplementation(async ruta => ({ data: String(ruta).includes('disponibilidad') ? { disponible: true, noches: 2, total: '450000', limpieza: '50000' } : alojamiento }))
})
async function cotizar() {
  mostrar()
  fireEvent.change(await screen.findByLabelText('Entrada'), { target: { value: '2099-06-01' } })
  fireEvent.change(screen.getByLabelText('Salida'), { target: { value: '2099-06-03' } })
  await usuario.click(screen.getByRole('button', { name: 'Comprobar disponibilidad' }))
  await screen.findByText('El alojamiento está disponible para estas fechas.')
  await usuario.click(screen.getByRole('checkbox'))
}
describe('Reserva integrada con formularios y consultas', () => {
  it('invalida la cotización si el huésped cambia las fechas', async () => {
    await cotizar()
    expect(screen.getByRole('button', { name: /Solicitar reserva/ })).toBeEnabled()
    fireEvent.change(screen.getByLabelText('Salida'), { target: { value: '2099-06-04' } })
    expect(screen.getByRole('button', { name: /Solicitar reserva/ })).toBeDisabled()
    expect(api.post).not.toHaveBeenCalled()
  })
  it('envía una única solicitud mientras espera respuesta', async () => {
    vi.mocked(api.post).mockImplementation(() => new Promise(() => {}))
    await cotizar()
    const boton = screen.getByRole('button', { name: /Solicitar reserva/ })
    await usuario.dblClick(boton)
    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1))
    expect(boton).toBeDisabled()
    expect(api.post).toHaveBeenCalledWith('reservas/', { alojamiento: 1, desde: '2099-06-01', hasta: '2099-06-03', huespedes: 1 })
  })
})
