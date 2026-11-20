import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import UbicacionContacto, { esEnlaceMaps } from '../componentes/UbicacionContacto'
import type { Alojamiento } from '../tipos'

describe('Ubicación y contacto del alojamiento', () => {
  it('abre el punto compartido y permite llamar al contacto publicado', () => {
    render(<UbicacionContacto alojamiento={{ calle: 'Calle 1', ubicacion: 'Villarrica', google_maps_url: 'https://maps.app.goo.gl/punto', telefono_contacto: '+595 981 123456' } as Alojamiento}/>)
    expect(screen.getByRole('link', { name: 'Ver ubicación en Google Maps' })).toHaveAttribute('href', 'https://maps.app.goo.gl/punto')
    expect(screen.getByRole('link', { name: '+595 981 123456' })).toHaveAttribute('href', 'tel:+595981123456')
  })
  it('distingue una búsqueda por dirección de un punto exacto no cargado', () => {
    render(<UbicacionContacto alojamiento={{ calle: '', ubicacion: 'San Bernardino' } as Alojamiento}/>)
    const enlace = screen.getByRole('link', { name: 'Buscar dirección en Google Maps' })
    expect(new URL(enlace.getAttribute('href')!).searchParams.get('query')).toBe('San Bernardino, Paraguay')
    expect(screen.getByText(/todavía no añadió un teléfono/)).toBeInTheDocument()
  })
  it('rechaza dominios suplantados y esquemas ejecutables', () => {
    expect(esEnlaceMaps('https://google.com.evil.test/maps')).toBe(false)
    expect(esEnlaceMaps('javascript:alert(1)')).toBe(false)
    expect(esEnlaceMaps('https://google.com/maps/place/Casa')).toBe(true)
  })
})
