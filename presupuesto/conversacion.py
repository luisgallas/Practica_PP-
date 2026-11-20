"""Conversación guiada con contexto firmado por la API, sin inventar datos."""
import re
from datetime import date
from django.utils import timezone
from . import agent
from .models import Propiedad, Reserva
from .services import get_available_properties


def ciudad_en(texto):
    ciudades = sorted(set(Propiedad.objects.values_list('ubicacion', flat=True)), key=len, reverse=True)
    conocida = next((ciudad for ciudad in ciudades if re.search(r'(?<!\w)' + re.escape(agent.normalize(ciudad)) + r'(?!\w)', texto)), None)
    if conocida:
        return conocida
    ubicacion = re.search(r'\ben\s+(.+?)(?=\s+(?:cuant[ao]s?|para|del|desde|hasta|tengo|hay|con|el|este)\b|[?.!,]|$)', texto)
    return ubicacion.group(1).strip() if ubicacion else None


def respuesta(texto, estado=None, **extra):
    return {'reply': texto, 'intent': 'guided_conversation', 'contexto': estado or {}, **extra}


def resumen(usuario, texto, estado):
    reservas = Reserva.objects.select_related('id_propiedad', 'id_huesped')
    if usuario.rol == 'anfitrion':
        reservas = reservas.filter(id_propiedad__id_anfitrion=usuario)
    elif usuario.rol == 'huesped':
        reservas = reservas.filter(id_huesped=usuario)
    ciudad = ciudad_en(texto) or (estado.get('ciudad') if estado.get('modo') == 'resumen' else None)
    if ciudad:
        reservas = reservas.filter(id_propiedad__ubicacion__iexact=ciudad)
    for valor in ['pendiente', 'confirmada', 'activa', 'completada', 'cancelada', 'rechazada']:
        if valor in texto:
            reservas = reservas.filter(estado=valor)
            break
    if 'este mes' in texto:
        hoy = timezone.localdate()
        reservas = reservas.filter(fecha_inicio__year=hoy.year, fecha_inicio__month=hoy.month)
    cantidad = reservas.count()
    alcance = 'del sistema' if usuario.rol == 'admin' else 'de tus alojamientos' if usuario.rol == 'anfitrion' else 'a tu nombre'
    detalle = '\n'.join(agent.format_reservation_summary(r) for r in reservas.order_by('-fecha_inicio')[:10])
    texto_respuesta = f'Encontré {cantidad} reservas {alcance}' + (f' en {ciudad}' if ciudad else '') + '.'
    if detalle:
        texto_respuesta += '\n' + detalle
    if cantidad > 10:
        texto_respuesta += '\nMostré las 10 más recientes. Podés ver todas en Reservas.'
    return respuesta(texto_respuesta, {'modo': 'resumen', 'ciudad': ciudad}, intent='reservations', data={'count': cantidad})


def conversar(usuario, mensaje, estado):
    texto = agent.normalize(mensaje)
    if texto in ['cancelar', 'descartar', 'empezar de nuevo', 'nueva consulta', 'no', 'no gracias']:
        return respuesta('Descarté la búsqueda. No creé ni cancelé ninguna reserva. ¿En qué te ayudo ahora?')
    if 'reservas' in texto or (estado.get('modo') == 'resumen' and ciudad_en(texto)):
        return resumen(usuario, texto, estado)
    iniciar = agent.wants_to_create_reservation(texto) or any(p in texto for p in ['disponib', 'busco', 'buscando', 'quiero una', 'quiero un', 'alojamiento', 'quinta', 'casa en'])
    if not estado.get('modo') == 'busqueda' and not iniciar:
        if any(p in texto for p in ['resena', 'amenities', 'mascota', 'servicios']):
            return agent.chat({'message': mensaje, 'user_id': usuario.pk})
        return respuesta('Puedo buscar un alojamiento por ciudad, fechas y cantidad de personas. También podés preguntarme por tus reservas. Por ejemplo: «Busco alojamiento en Villarrica» o «¿Cuántas reservas tengo en Villarrica?»')
    estado = dict(estado) if estado.get('modo') == 'busqueda' else {'modo': 'busqueda'}
    ciudad = ciudad_en(texto)
    if ciudad and ciudad != estado.get('ciudad'):
        estado.update(ciudad=ciudad)
        estado.pop('propiedad', None)
        estado.pop('opciones', None)
    for palabra, tipo in [('departamento', 'departamento'), ('habitacion', 'habitacion'), ('quinta', 'quinta'), ('casa', 'casa_entera')]:
        if palabra in texto and estado.get('paso') != 'opcion':
            estado['tipo'] = tipo
            break
    if estado.get('paso') == 'ciudad' and not ciudad and not iniciar:
        estado['ciudad'] = mensaje.strip()
    for propiedad in Propiedad.objects.filter(estado='disponible'):
        if agent.normalize(propiedad.titulo) in texto:
            estado.update(propiedad=propiedad.pk, ciudad=propiedad.ubicacion)
            break
    # Una elección numérica solo se interpreta como opción en ese paso.
    if estado.get('paso') == 'opcion':
        ordinales = {'primera': 1, 'segunda': 2, 'tercera': 3, 'cuarta': 4, 'quinta': 5}
        numero = re.fullmatch(r'(?:la |opcion |elijo |quiero la )?(\d+)', texto)
        indice = int(numero.group(1)) if numero else next((v for k, v in ordinales.items() if k in texto), 0)
        if indice and indice <= len(estado.get('opciones', [])):
            estado['propiedad'] = estado['opciones'][indice - 1]
    personas = re.search(r'(\d+)\s*(?:personas?|huespedes?|adultos?)', texto)
    if not personas and estado.get('paso') == 'personas':
        personas = re.fullmatch(r'(?:somos |para )?(\d+)', texto)
    if personas:
        cantidad = int(personas.group(1))
        if not 1 <= cantidad <= 100:
            return respuesta('Indicá entre 1 y 100 huéspedes en total.', estado)
        estado['personas'] = cantidad
    # Fechas sueltas nunca implican automáticamente una noche.
    tiene_fecha = bool(re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+de\s+[a-z]+', texto))
    if estado.get('paso') == 'anio' and re.fullmatch(r'(?:de |del )?20\d{2}', texto):
        anio = re.search(r'20\d{2}', texto).group()
        mensaje = estado.pop('fechas_pendientes') + ' de ' + anio
        estado['paso'] = estado.pop('paso_fecha', 'entrada')
        texto = agent.normalize(mensaje)
        tiene_fecha = True
    if tiene_fecha:
        if not re.search(r'\b20\d{2}\b', texto):
            estado.update(paso_fecha=estado.get('paso'), paso='anio', fechas_pendientes=mensaje)
            return respuesta('¿De qué año son esas fechas?', estado)
        try:
            inicio, fin = agent.parse_date_range(mensaje)
            # El analizador original omite el año en fechas individuales con mes escrito.
            if inicio and not re.search(r'\b(al|hasta)\b|\d{1,2}\s*-\s*\d{1,2}\s+de', texto):
                anio = int(re.search(r'\b(20\d{2})\b', texto).group(1))
                inicio = inicio.replace(year=anio)
                if estado.get('paso') == 'salida' or 'salida' in texto:
                    estado['salida'] = inicio.isoformat()
                else:
                    estado['entrada'] = inicio.isoformat()
                    estado.pop('salida', None)
            elif inicio:
                estado.update(entrada=inicio.isoformat(), salida=fin.isoformat())
        except ValueError:
            return respuesta('Esa fecha no es válida. Escribí entrada y salida con año, por ejemplo 20/12/2027 al 22/12/2027.', estado)
    for campo, pregunta in [('ciudad', '¿En qué ciudad querés alojarte?'), ('entrada', '¿Qué fecha de entrada buscás? Podés enviar entrada y salida juntas, con año (DD/MM/AAAA al DD/MM/AAAA).'), ('salida', '¿Qué fecha de salida querés? Incluí día, mes y año.'), ('personas', '¿Para cuántos huéspedes en total, incluyendo niños?')]:
        if not estado.get(campo):
            estado['paso'] = campo if campo != 'personas' else 'personas'
            return respuesta(pregunta, estado)
    inicio, fin = date.fromisoformat(estado['entrada']), date.fromisoformat(estado['salida'])
    if inicio < timezone.localdate() or not 1 <= (fin - inicio).days <= 365:
        estado.pop('entrada', None)
        estado.pop('salida', None)
        estado['paso'] = 'entrada'
        return respuesta('Revisemos las fechas: la entrada no puede estar en el pasado y la salida debe ser posterior, hasta 365 noches. ¿Qué entrada y salida querés?', estado)
    disponibles = [p for p in get_available_properties(inicio, fin, estado['personas']) if agent.normalize(p['ubicacion']) == agent.normalize(estado['ciudad'])]
    tipo = estado.get('tipo')
    if tipo == 'quinta':
        ids = {p.pk for p in Propiedad.objects.filter(estado='disponible') if 'quinta' in agent.normalize(p.titulo + ' ' + p.descripcion)}
        disponibles = [p for p in disponibles if p['id'] in ids]
    elif tipo:
        disponibles = [p for p in disponibles if p['tipo_alojamiento'].startswith(tipo)]
    if not disponibles:
        estado.pop('propiedad', None)
        estado.pop('opciones', None)
        estado['paso'] = 'entrada'
        return respuesta(f"No encontré alojamientos que coincidan con tu búsqueda en {estado['ciudad']} para {estado['personas']} personas del {inicio} al {fin}. Podés cambiar las fechas, la ciudad o la cantidad de personas.", estado)
    elegida = next((p for p in disponibles if p['id'] == estado.get('propiedad')), None)
    if not elegida:
        estado.pop('propiedad', None)
        estado.update(paso='opcion', opciones=[p['id'] for p in disponibles[:5]])
        opciones = '\n'.join(f"{i}. {p['titulo']} — Total Gs. {int(p['precio_total']):,}" for i, p in enumerate(disponibles[:5], 1))
        return respuesta(f"Encontré estas opciones del {inicio} al {fin} para {estado['personas']} personas en {estado['ciudad']}:\n{opciones}\nElegí un número o el nombre del alojamiento. Son alojamientos disponibles; revisá el detalle para verificar el tipo y los servicios que necesitás.", estado, opciones=[{'id': p['id'], 'titulo': p['titulo']} for p in disponibles[:5]])
    estado['paso'] = 'confirmacion'
    if usuario.rol != 'huesped':
        return respuesta(f"{elegida['titulo']} está disponible. Total: Gs. {elegida['precio_total']}. Tu rol permite consultar; solo las cuentas de huéspedes pueden solicitar reservas.", estado)
    propiedad = Propiedad.objects.get(pk=elegida['id'])
    reglas = ', '.join([('admite' if propiedad.permite_mascotas else 'no admite') + ' mascotas', ('permite' if propiedad.permite_fumar else 'no permite') + ' fumar', ('permite' if propiedad.permite_fiestas else 'no permite') + ' fiestas'])
    return respuesta(f"Revisá tu solicitud:\nAlojamiento: {elegida['titulo']}\nCiudad: {elegida['ubicacion']}\nEntrada: {inicio} · Salida: {fin}\nHuéspedes: {estado['personas']}\nTotal: Gs. {int(elegida['precio_total']):,} (incluye limpieza)\nCancelación: {elegida['politica_cancelacion']}\nReglas: {reglas}.\n¿Confirmás la solicitud y estas condiciones? Quedará pendiente de aceptación del anfitrión. No se realiza ningún cobro online. Podés corregir los datos o escribir «descartar».", estado, intent='create_reservation_needs_confirmation', pending_action={'type': 'create_reservation', 'data': {'property_id': elegida['id'], 'guest_id': usuario.pk, 'start_date': str(inicio), 'end_date': str(fin), 'guests': estado['personas'], 'quoted_total': elegida['precio_total']}})
