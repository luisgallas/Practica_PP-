import os
import sys
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VIDEO_DEPS = ROOT / ".video_deps"
if VIDEO_DEPS.exists():
    sys.path.insert(0, str(VIDEO_DEPS))

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1280, 720
FPS = 1


def font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


TITLE = font(48, True)
SUBTITLE = font(30, True)
BODY = font(26)
SMALL = font(21)
CODE = font(22)


def wrap(draw, text, max_width, fnt):
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for word in paragraph.split():
            candidate = (current + " " + word).strip()
            if draw.textlength(candidate, font=fnt) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def draw_wrapped(draw, text, xy, max_width, fnt, fill, line_gap=8):
    x, y = xy
    for line in wrap(draw, text, max_width, fnt):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def make_frame(slide, frame_no, total_frames):
    img = Image.new("RGB", (WIDTH, HEIGHT), "#f7f7f4")
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, WIDTH, 92), fill="#153e35")
    draw.text((54, 24), "GuairaDevs Booking - Agente IA", font=SUBTITLE, fill="#ffffff")
    draw.text((WIDTH - 270, 32), "Demo de entrega", font=SMALL, fill="#d9f2ea")

    draw.text((72, 130), slide["title"], font=TITLE, fill="#18201d")
    y = 205
    if slide.get("subtitle"):
        y = draw_wrapped(draw, slide["subtitle"], (76, y), 1060, BODY, "#32433e", 10) + 12

    for bullet in slide.get("bullets", []):
        draw.ellipse((82, y + 10, 94, y + 22), fill="#1d7f63")
        y = draw_wrapped(draw, bullet, (110, y), 1040, BODY, "#1d2925", 10) + 4

    if slide.get("code"):
        y += 10
        draw.rounded_rectangle((76, y, WIDTH - 76, HEIGHT - 104), radius=10, fill="#101715")
        code_y = y + 28
        for line in slide["code"].split("\n"):
            draw.text((106, code_y), line, font=CODE, fill="#d8fff2")
            code_y += 31

    progress_w = WIDTH - 140
    progress_x = 70
    progress_y = HEIGHT - 42
    draw.rectangle((progress_x, progress_y, progress_x + progress_w, progress_y + 8), fill="#d5ded9")
    draw.rectangle(
        (progress_x, progress_y, progress_x + int(progress_w * frame_no / max(total_frames - 1, 1)), progress_y + 8),
        fill="#1d7f63",
    )

    return np.array(img)


def main():
    slides = [
        {
            "duration": 20,
            "title": "Objetivo",
            "subtitle": "Integrar un agente util para huespedes y anfitriones, conectado al backend real.",
            "bullets": [
                "Consulta propiedades, amenities y disponibilidad.",
                "Prepara reservas, pero pide confirmacion antes de crear.",
                "Permite a anfitriones revisar reservas y pendientes.",
            ],
        },
        {
            "duration": 22,
            "title": "Arquitectura",
            "subtitle": "Usuario -> Agente -> Backend Django REST -> Servicios -> Base de datos.",
            "bullets": [
                "Endpoint principal: POST /api/agent/chat/.",
                "Endpoints de soporte: properties, availability, reservations y amenities.",
                "La informacion sale de db.sqlite3 o de la base configurada en .env.",
            ],
        },
        {
            "duration": 24,
            "title": "Rol claro",
            "subtitle": "El system prompt limita el alcance del agente.",
            "bullets": [
                "No responde temas fuera de la plataforma.",
                "No busca online.",
                "Si falta un dato, lo pide.",
                "Crear o modificar reservas requiere confirmacion explicita.",
            ],
        },
        {
            "duration": 28,
            "title": "Consulta de disponibilidad",
            "code": 'curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" ^\n  -H "Content-Type: application/json" ^\n  -d "{\\"message\\":\\"Hay propiedades disponibles del 20 al 25 de julio para 2 personas?\\"}"\n\nRespuesta: encuentra propiedades reales, precios estimados y amenities.',
        },
        {
            "duration": 24,
            "title": "Amenities y reglas",
            "code": 'curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" ^\n  -H "Content-Type: application/json" ^\n  -d "{\\"message\\":\\"Que amenities tiene la Quinta Guaira? Acepta mascotas?\\"}"\n\nRespuesta: informa amenities cargados y aclara si mascotas figura como permitido.',
        },
        {
            "duration": 30,
            "title": "Reserva segura",
            "code": 'curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" ^\n  -H "Content-Type: application/json" ^\n  -d "{\\"message\\":\\"Quiero reservar esta propiedad para el 15 de agosto en la Quinta Guaira\\",\\"user_id\\":6}"\n\nRespuesta: devuelve pending_action y pregunta: Confirmas que la cree?\nTodavia no escribe en la base.',
        },
        {
            "duration": 26,
            "title": "Vista de anfitrion",
            "code": 'curl.exe -X POST "http://127.0.0.1:8000/api/agent/chat/" ^\n  -H "Content-Type: application/json" ^\n  -d "{\\"message\\":\\"Hay reservas pendientes de confirmar?\\",\\"user_id\\":2}"\n\nRespuesta: lista o cuenta reservas reales filtradas por anfitrion.',
        },
        {
            "duration": 26,
            "title": "Verificacion",
            "subtitle": "La entrega queda reproducible desde el repositorio.",
            "bullets": [
                "Documentacion y Mermaid: docs/agent_entrega.md.",
                "Config Dify/Botpress: docs/dify_botpress_config.md.",
                "Guion de grabacion: docs/video_guion.md.",
                "Tests: python manage.py test presupuesto -> 3 tests OK.",
            ],
        },
    ]

    frames = []
    total_frames = sum(slide["duration"] * FPS for slide in slides)
    frame_no = 0
    output = ROOT / "docs" / "video_demo.mp4"
    output.parent.mkdir(exist_ok=True)

    with imageio.get_writer(output, fps=FPS, codec="libx264", quality=8, macro_block_size=16) as writer:
        for slide in slides:
            for _ in range(slide["duration"] * FPS):
                writer.append_data(make_frame(slide, frame_no, total_frames))
                frame_no += 1

    print(output)


if __name__ == "__main__":
    main()
