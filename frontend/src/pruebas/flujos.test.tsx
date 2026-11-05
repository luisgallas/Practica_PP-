import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import usuario from '@testing-library/user-event'
import { Boton, Campo, ErrorConsulta } from '../componentes/Base'
import { validarFotos } from '../componentes/GestorFotos'
import { esquemaFechas } from '../paginas/Reservar'

describe('Controles accesibles y operaciones', () => {
  it('bloquea envíos repetidos mientras procesa', async () => {
    const accion = vi.fn()
    render(<Boton ocupado onClick={accion}>Reservar</Boton>)
    const boton = screen.getByRole('button', { name: /Procesando/ })
    await usuario.click(boton)
    expect(accion).not.toHaveBeenCalled()
    expect(boton).toHaveAttribute('aria-busy', 'true')
  })
  it('asocia la etiqueta y el error con el campo', () => {
    render(<Campo etiqueta="Entrada" error="La fecha ya pasó."/>)
    const campo = screen.getByLabelText('Entrada')
    expect(campo).toHaveAttribute('aria-invalid', 'true')
    expect(campo).toHaveAccessibleDescription('La fecha ya pasó.')
  })
  it('permite reintentar una consulta fallida', async () => {
    const reintentar = vi.fn()
    render(<ErrorConsulta error={new Error('Sin conexión')} reintentar={reintentar}/>)
    await usuario.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(reintentar).toHaveBeenCalledOnce()
  })
})
describe('Validaciones previas a enviar', () => {
  it('cuenta las imágenes existentes al aplicar el máximo de cinco', () => {
    const foto = new File(['imagen'], 'foto.png', { type: 'image/png' })
    expect(validarFotos([foto, foto], 4)).toMatch(/5 fotos/)
    expect(validarFotos([foto], 4)).toBe('')
  })
  it('rechaza SVG y archivos demasiado grandes', () => {
    expect(validarFotos([new File(['<svg/>'], 'x.svg', { type: 'image/svg+xml' })], 0)).toMatch(/JPEG/)
    expect(validarFotos([new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'x.jpg', { type: 'image/jpeg' })], 0)).toMatch(/5 MB/)
  })
  it('rechaza fechas pasadas, salida anterior y cero huéspedes', () => {
    expect(esquemaFechas.safeParse({ desde: '2000-01-01', hasta: '2000-01-02', huespedes: 1 }).success).toBe(false)
    expect(esquemaFechas.safeParse({ desde: '2099-02-02', hasta: '2099-02-01', huespedes: 1 }).success).toBe(false)
    expect(esquemaFechas.safeParse({ desde: '2099-02-01', hasta: '2099-02-02', huespedes: 0 }).success).toBe(false)
    expect(esquemaFechas.safeParse({ desde: '2099-02-01', hasta: '2099-02-02', huespedes: 2 }).success).toBe(true)
  })
})
