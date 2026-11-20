import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Autenticacion from '../paginas/Autenticacion'
import Volver from '../componentes/Volver'
import type { Rol } from '../tipos'

const sesion = vi.hoisted(() => ({ iniciar: vi.fn(), usuario: { rol: 'huesped' as Rol } }))
vi.mock('../contextos/Sesion', () => ({ usarSesion: () => sesion }))
vi.mock('../servicios/api', () => ({ registrar: vi.fn(), mensajeError: () => 'Error de ingreso' }))
beforeEach(() => vi.clearAllMocks())
describe('Inicio y navegación por rol', () => {
  it.each(['huesped', 'anfitrion', 'admin'] as Rol[])('envía a %s a su pantalla principal aunque el destino previo sea IA', async rol => {
    sesion.iniciar.mockResolvedValue({ rol })
    render(<MemoryRouter initialEntries={['/ingresar?siguiente=%2Fasistente']}><Routes><Route path="/ingresar" element={<Autenticacion/>}/><Route path="/alojamientos" element={<h1>Explorar alojamientos</h1>}/><Route path="/panel" element={<h1>Mi panel</h1>}/><Route path="/asistente" element={<h1>Chat</h1>}/></Routes></MemoryRouter>)
    fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'prueba' } })
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: 'MiClave123!' } })
    await userEvent.click(screen.getByRole('button', { name: /Ingresar/ }))
    expect(await screen.findByRole('heading', { name: rol === 'huesped' ? 'Explorar alojamientos' : 'Mi panel' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Chat' })).not.toBeInTheDocument()
  })
  it.each(['huesped', 'anfitrion', 'admin'] as Rol[])('permite a %s salir del chat incluso al abrirlo directamente', async rol => {
    sesion.usuario.rol = rol
    render(<MemoryRouter initialEntries={['/asistente']}><Routes><Route path="/asistente" element={<Volver/>}/><Route path="/alojamientos" element={<h1>Explorar</h1>}/><Route path="/panel" element={<h1>Panel</h1>}/></Routes></MemoryRouter>)
    await userEvent.click(screen.getByRole('link', { name: /Volver/ }))
    expect(await screen.findByRole('heading', { name: rol === 'huesped' ? 'Explorar' : 'Panel' })).toBeInTheDocument()
  })
  it.each([
    ['/reservar/12', '/alojamientos/12'],
    ['/gestion/alojamientos/nuevo', '/gestion/alojamientos'],
    ['/gestion/alojamientos/12', '/gestion/alojamientos'],
    ['/registro', '/'], ['/ingresar', '/'], ['/confirmacion/12', '/reservas'],
  ])('ofrece una salida del formulario %s', (ruta, destino) => {
    render(<MemoryRouter initialEntries={[ruta]}><Volver/></MemoryRouter>)
    expect(screen.getByRole('link', { name: /Volver/ })).toHaveAttribute('href', destino)
  })
})
