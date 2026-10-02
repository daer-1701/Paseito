"""Datos reales del Paseo Aranjuez recopilados de fuentes públicas (octubre 2026).

- Lugares: directorio oficial paseoaranjuez.com/stores, procesado por scripts/importar_paseo.py
  y guardado en app/datos/lugares.json (editable a mano para completar locales y horarios).
- Eventos: cronograma oficial de la Hackathon By Paseo 2026.
- Preguntas frecuentes: sitio oficial, Pulso Empresarial, Los Tiempos, Google Maps/Waze.
Productos y promociones quedan vacíos hasta relevarlos con cada tienda.
"""

import json
from datetime import date
from pathlib import Path

from sqlmodel import Session, select

from .models import Evento, Faq, Tienda

LUGARES_JSON = Path(__file__).resolve().parent / "datos" / "lugares.json"

EVENTOS = [
    dict(nombre="Hackathon By Paseo 2026: inauguración y presentación de retos",
         descripcion="Inicio de la hackathon: inauguración, palabras del CEO de On Business y presentación de retos.",
         fecha=date(2026, 10, 2), hora_inicio="09:00", hora_fin="11:00", lugar="Paseo Aranjuez"),
    dict(nombre="Hackathon: charla de oratoria a cargo de Zontes",
         descripcion="Charla de oratoria para los equipos participantes.",
         fecha=date(2026, 10, 2), hora_inicio="11:00", hora_fin="12:00", lugar="Paseo Aranjuez"),
    dict(nombre="Hackathon: charla «Cómo patentar un producto digital»",
         descripcion="Charla abierta durante la segunda jornada de la hackathon.",
         fecha=date(2026, 10, 3), hora_inicio="11:00", hora_fin="12:00", lugar="Paseo Aranjuez"),
    dict(nombre="Hackathon: charla «UX/UI para desarrolladores»",
         descripcion="Charla sobre diseño de experiencia e interfaces.",
         fecha=date(2026, 10, 3), hora_inicio="16:00", hora_fin="17:00", lugar="Paseo Aranjuez"),
    dict(nombre="Demo Day de la Hackathon By Paseo 2026",
         descripcion="Presentaciones de los equipos concursantes en dos bloques (11:15 a 13:00 y 14:00 a 16:30).",
         fecha=date(2026, 10, 4), hora_inicio="11:15", hora_fin="16:30", lugar="Paseo Aranjuez"),
    dict(nombre="Premiación de la Hackathon By Paseo 2026",
         descripcion="Oportunidades ON WORK, anuncio de ganadores, ceremonia de premiación y networking.",
         fecha=date(2026, 10, 4), hora_inicio="17:00", hora_fin="18:00", lugar="Paseo Aranjuez"),
]

FAQS = [
    ("¿Dónde queda el Paseo Aranjuez y cómo llego?",
     "Está en la avenida América número 488, esquina calle Pantaleón Dalence, en la zona norte de Cochabamba.",
     "direccion,ubicacion,llegar,donde queda,como llego,avenida america"),
    ("¿Cuál es el horario del Paseo?",
     "Las tiendas suelen atender de lunes a sábado de 10:00 a 22:00 y los domingos de 11:00 a 21:00. "
     "La zona gastronómica puede extenderse los viernes y sábados. Cada local puede tener su propio horario.",
     "horario,abre,cierra,hora,atencion,domingo"),
    ("¿Hay estacionamiento?",
     "Sí, el Paseo tiene estacionamiento propio en cinco semisótanos, con señalización de espacios libres. "
     "Ofrece parqueo validado al consumir en restaurantes y cafeterías o al hacer compras.",
     "estacionamiento,parqueo,parquear,auto,garaje,parking,validado"),
    ("¿Cómo están distribuidos los pisos?",
     "Planta baja, primer y segundo piso son de tiendas; el tercer piso es el Mercado Gastronómico; el cuarto "
     "piso es El Cuarto, la terraza gourmet; y desde el quinto piso están las torres de oficinas.",
     "pisos,distribucion,niveles,plantas,mapa,donde esta"),
    ("¿Cómo contacto al Paseo Aranjuez?",
     "Por WhatsApp al +591 61795513 o al correo info@paseoaranjuez.com. En redes es @paseoaranjuez en "
     "Instagram y Facebook, y @paseoaranjuezoficial en TikTok.",
     "contacto,telefono,whatsapp,correo,email,redes sociales,informacion,atencion al cliente"),
    ("¿Cómo reservo una mesa en El Cuarto?",
     "Las reservas de El Cuarto, la terraza gourmet del cuarto piso, se hacen por WhatsApp al +591 61795511.",
     "reserva,reservar,mesa,el cuarto,terraza,cumpleaños,celebracion"),
    ("¿Hay oficinas o cowork?",
     "Sí. Desde el quinto piso hay dos torres empresariales con oficinas de distintos tipos y un cowork "
     "empresarial con acceso 24/7 y wifi de alta velocidad. Informes por WhatsApp al +591 70721225.",
     "oficina,oficinas,cowork,coworking,alquiler,sala de reuniones,trabajar,torre"),
    ("¿Qué hay para niños?",
     "El Mercado Gastronómico del tercer piso tiene áreas de recreación y entretenimiento para niños y "
     "jóvenes, y hay jugueterías como Fair Play Kids en planta baja, y Muy Mimados y TUC TOYS en el primer piso.",
     "niños,infantil,juegos,familia,recreacion,jugueteria"),
    ("¿Qué actividades culturales hay?",
     "El Paseo tiene una galería de arte con obras de artistas nacionales y espacios para artistas. "
     "Organiza actividades como Cinema Lounge, Feria del Libro, desfiles y actividades semanales.",
     "arte,galeria,cultura,cine,cinema,feria del libro,desfiles,actividades,eventos"),
    ("¿Se puede ir con mascotas?",
     "El Paseo Aranjuez promueve el bienestar de las mascotas. Para conocer las condiciones de ingreso, "
     "consulta por WhatsApp al +591 61795513.",
     "mascotas,perro,gato,pet friendly,animales"),
    ("¿Qué es el Paseo Aranjuez?",
     "Es un centro comercial y empresarial inaugurado en noviembre de 2020: un edificio inteligente y "
     "ecológico de 16 pisos y cinco semisótanos, con más de 60 locales, galería de arte, mercado "
     "gastronómico, terraza gourmet y torres de oficinas.",
     "paseo aranjuez,historia,que es,edificio,inteligente,ecologico,sobre el paseo"),
]


def sembrar(db: Session) -> bool:
    """Carga los datos si la base está vacía. Devuelve True si sembró."""
    if db.exec(select(Tienda)).first():
        return False

    lugares = json.loads(LUGARES_JSON.read_text(encoding="utf-8"))
    db.add_all([Tienda(**lugar) for lugar in lugares])
    db.add_all([Evento(**e) for e in EVENTOS])
    db.add_all([Faq(pregunta=p, respuesta=r, etiquetas=e) for p, r, e in FAQS])
    db.commit()
    return True
