export const guaranies = (valor: string | number) => `Gs. ${new Intl.NumberFormat('es-PY', { maximumFractionDigits: 0 }).format(Number(valor))}`
export const fecha = (valor: string) => new Intl.DateTimeFormat('es-PY', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(valor.includes('T') ? valor : valor + 'T12:00:00'))
export const hoy = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Asuncion', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
export const tipos: Record<string, string> = { casa_entera: 'Casa entera', departamento: 'Departamento', habitacion_privada: 'Habitación privada', habitacion_compartida: 'Habitación compartida' }
