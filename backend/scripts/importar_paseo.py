"""Descarga el directorio oficial de https://paseoaranjuez.com/stores y genera app/datos/lugares.json.

Uso:  python scripts/importar_paseo.py
Los datos que el directorio no trae (número de local, horarios por tienda) se completan con
AJUSTES; todo lo que no esté confirmado queda con horario_confirmado = false.
"""

import json
import re
import urllib.request
from pathlib import Path

URL = "https://paseoaranjuez.com"
DESTINO = Path(__file__).resolve().parent.parent / "app" / "datos" / "lugares.json"

PISOS = {
    "Planta Baja": "Planta Baja",
    "Primer Piso": "Primer Piso",
    "Segundo Piso": "Segundo Piso",
    "Tercer Piso": "Tercer Piso",
    "Cuarto Piso": "Cuarto Piso",
}
SECTOR_POR_PISO = {
    "Tercer Piso": "Mercado Gastronómico",
    "Cuarto Piso": "El Cuarto (terraza gourmet)",
}
# Horario general de tiendas según los listados públicos de los locales (Google Maps).
HORARIO_POR_PISO = {
    "Planta Baja": ("10:00", "22:00", "11:00", "21:00"),
    "Primer Piso": ("10:00", "22:00", "11:00", "21:00"),
    "Segundo Piso": ("10:00", "22:00", "11:00", "21:00"),
    "Tercer Piso": ("11:00", "22:00", "11:00", "22:00"),
    "Cuarto Piso": ("12:00", "22:00", "12:00", "22:00"),
}

# rubro del directorio -> (categoría legible, etiquetas de búsqueda)
RUBROS = {
    "calzado": ("Calzado", "zapatos,zapateria,zapatillas,calzado,sandalias"),
    "comida": ("Comida", "comida,postres,dulces,cafe"),
    "tecnologia": ("Tecnología", "celulares,accesorios,audifonos,cargadores,tecnologia,fundas"),
    "jugueteria": ("Juguetería", "juguetes,niños,regalo,juegos"),
    "hogar": ("Hogar", "hogar,decoracion,cocina,menaje,regalo"),
    "joyeria": ("Joyería", "joyas,anillos,collares,aretes,pulseras,regalo"),
    "ropa": ("Ropa", "ropa,moda,vestir"),
    "ropa interior": ("Ropa interior y cosméticos", "ropa interior,lenceria,pijamas,cosmeticos,regalo"),
    "deportes": ("Deportes", "deportes,zapatillas,ropa deportiva,deportivo"),
    "optica": ("Óptica", "lentes,gafas,anteojos,gafas de sol,monturas,examen visual"),
    "ropa infantil": ("Ropa infantil", "ropa de niños,niños,bebes,infantil"),
    "cosmeticos": ("Cosméticos", "maquillaje,cosmeticos,belleza,cuidado de la piel,regalo"),
    "jeans": ("Jeans", "jeans,pantalones,ropa"),
    "relojeria": ("Relojería", "relojes,accesorios,regalo"),
    "artesanias": ("Artesanías y diseño boliviano", "artesania,souvenirs,recuerdos,regalo,diseño boliviano"),
    "accesorios": ("Accesorios", "accesorios,bisuteria,carteras,regalo"),
    "ropa de hombre": ("Ropa de hombre", "ropa de hombre,camisas,trajes,pantalones,caballero"),
    "bebes": ("Bebés", "bebes,ropa de bebe,coches,maternidad"),
    "lenceria": ("Lencería", "lenceria,ropa interior"),
    "juegos": ("Videojuegos", "videojuegos,consolas,gaming,juegos"),
    "perfumeria": ("Perfumería", "perfumes,fragancias,regalo"),
    "cuidado personal": ("Cuidado personal", "uñas,manicure,pedicure,belleza"),
    "telecomunicaciones": ("Telecomunicaciones", "telefonia,chip,planes,internet,celulares,lineas"),
    "ropa y accesorios": ("Mochilas, ropa y accesorios", "mochilas,maletas,ropa,accesorios,viaje"),
}

# Datos verificados en fuentes públicas o deducibles del nombre del local.
AJUSTES = {
    "Cinnabon": dict(categoria="Cafetería y repostería", etiquetas="rolls de canela,postres,cafe,dulce,merienda"),
    "PUMA": dict(etiquetas="deportes,zapatillas,ropa deportiva"),
    "Floristeria Flor de Amor": dict(nombre="Floristería Flor de Amor", categoria="Floristería",
                                     etiquetas="flores,arreglos florales,ramos,regalo"),
    "Pauker": dict(nombre="Ópticas Pauker", hora_apertura="10:00", hora_cierre="21:00",
                   apertura_domingo="", cierre_domingo="", horario_confirmado=True),
    "Lili Pink": dict(hora_apertura="10:00", hora_cierre="22:00", apertura_domingo="10:00",
                      cierre_domingo="21:00", horario_confirmado=True),
    "BELU Boutique": dict(categoria="Ropa de mujer y accesorios",
                          etiquetas="ropa de mujer,moda,accesorios,joyas,bisuteria,Ohanna Accesorios",
                          referencia="Al lado del ascensor sur", horario_confirmado=True,
                          descripcion="Boutique de ropa femenina; dentro funciona Ohanna Accesorios (joyería)."),
    "Sajama": dict(categoria="Accesorios de madera bolivianos",
                   etiquetas="relojes,gafas de sol,monturas,madera,diseño boliviano,regalo",
                   descripcion="Primera marca boliviana de relojes, gafas de sol y monturas trabajadas en madera.",
                   apertura_domingo="10:00", cierre_domingo="22:00", horario_confirmado=True),
    "Totto": dict(local="203", hora_apertura="10:00", hora_cierre="22:00",
                  apertura_domingo="10:00", cierre_domingo="22:00", horario_confirmado=True),
    "Solo Pastas": dict(local="301", categoria="Comida italiana", etiquetas="pastas,italiana,almuerzo,cena",
                        hora_apertura="11:00", hora_cierre="22:00", apertura_domingo="11:00",
                        cierre_domingo="22:00", horario_confirmado=True),
    "Bolivia Fitness": dict(categoria="Fitness", etiquetas="fitness,deporte,gimnasio,suplementos"),
    "Chipotle Mexican Food": dict(categoria="Comida mexicana", etiquetas="mexicana,tacos,burritos,nachos"),
    "Helados Vacafría": dict(categoria="Heladería", etiquetas="helados,postre,dulce"),
    "PARRILLEROS": dict(nombre="Parrilleros", categoria="Parrilla", etiquetas="parrilla,carne,asado,almuerzo"),
    "Yummy Candy Bar": dict(categoria="Dulces", etiquetas="dulces,golosinas,caramelos,regalo"),
    "Almacén de Pizzas": dict(categoria="Pizzería"),
    "Açaí Golden": dict(categoria="Açaí y postres"),
    "Bypass Burger": dict(categoria="Hamburguesas"),
    "La Sanguchería Cafe": dict(nombre="La Sanguchería Café", categoria="Sándwiches y hamburguesas"),
    "Tunari Express": dict(categoria="Comida nacional"),
    "Waffle King": dict(categoria="Waffles y postres"),
    "Flavor Burst": dict(categoria="Heladería y cafetería"),
    "Brocheta King": dict(categoria="Brochetas y parrilla"),
    "CAYENNA": dict(nombre="Cayenna Bistro Café", categoria="Bistró y coctelería"),
    "Churros Calientes": dict(categoria="Churrería y cafetería"),
    "Monalisa Bier Haus": dict(categoria="Cervecería y restaurante"),
    "Patanegra, cocina española": dict(nombre="Patanegra", categoria="Cocina española"),
    "Rissi's": dict(categoria="Comida italiana"),
    "APPLE LAND": dict(nombre="Apple Land", etiquetas="iphone,apple,celulares,accesorios,tecnologia"),
    "Tigo": dict(tipo="servicio"),
    "Nails Express Gel": dict(tipo="servicio"),
    "Ópticas Pauker": dict(tipo="servicio"),
}

ESPACIOS = [
    dict(nombre="Mercado Gastronómico", tipo="restaurante", categoria="Patio de comidas",
         descripcion=("Lounge gastronómico con comida estilo exprés, unos 450 asientos, áreas lounge, "
                      "coworking, recreación y entretenimiento para niños y jóvenes."),
         piso="Tercer Piso", sector="Mercado Gastronómico",
         etiquetas="patio de comidas,comida,almorzar,comer,niños,coworking,sentarse",
         instagram="https://www.instagram.com/mercado_gastronomico_bypaseo/",
         hora_apertura="11:00", hora_cierre="22:00", apertura_domingo="11:00", cierre_domingo="22:00"),
    dict(nombre="El Cuarto", tipo="restaurante", categoria="Terraza gourmet y bar",
         descripcion=("Terraza gourmet del cuarto piso con cabinas de restaurantes especializados, servicio de "
                      "bar por la noche y vista al Tunari y al Cristo de la Concordia. Acepta reservas por "
                      "WhatsApp al +591 61795511."),
         piso="Cuarto Piso", sector="El Cuarto (terraza gourmet)", telefono="61795511",
         whatsapp="https://wa.me/59161795511",
         etiquetas="terraza,bar,tragos,cocteles,cena,vista,reserva,gourmet,after office",
         instagram="https://www.instagram.com/elcuartobypaseo/",
         hora_apertura="12:00", hora_cierre="22:00", apertura_domingo="12:00", cierre_domingo="22:00"),
    dict(nombre="Paseo Aranjuez Office", tipo="oficina", categoria="Torres empresariales y cowork",
         descripcion=("Dos torres de oficinas a partir del quinto piso, con oficinas tipo A a D y cowork "
                      "empresarial con acceso 24/7, wifi de alta velocidad y salas de reunión."),
         piso="Quinto piso en adelante", sector="Torres empresariales", telefono="70721225",
         whatsapp="https://wa.me/59170721225",
         etiquetas="oficinas,cowork,coworking,sala de reuniones,alquiler de oficinas,trabajo",
         hora_apertura="00:00", hora_cierre="23:59", apertura_domingo="00:00", cierre_domingo="23:59"),
    dict(nombre="Galería de Arte", tipo="servicio", categoria="Arte y cultura",
         descripcion=("Espacio dedicado a exponer pinturas, esculturas e instalaciones de artistas "
                      "nacionales; es de acceso libre para el público."),
         piso="Por confirmar", sector="", etiquetas="arte,galeria,exposicion,cultura,pinturas,esculturas",
         instagram="https://www.instagram.com/galeriadeartebo/"),
]


def arreglar_texto(texto: str) -> str:
    """El directorio devuelve UTF-8 doblemente codificado ('TecnologÃ­a')."""
    if not texto or "Ã" not in texto and "Â" not in texto:
        return texto
    for codec in ("cp1252", "latin-1"):
        try:
            return texto.encode(codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return texto


def normalizar(texto: str) -> str:
    import unicodedata
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").strip()


def numero_whatsapp(url: str) -> str:
    m = re.search(r"(?:wa\.me/|phone=)\+?(\d{8,15})", url or "")
    return m.group(1) if m else ""


def convertir(tienda: dict) -> dict:
    nombre = arreglar_texto(tienda["title"]).strip()
    piso = PISOS.get(tienda.get("floor"), tienda.get("floor") or "Por confirmar")
    rubros = [arreglar_texto(c).strip() for c in tienda.get("categories") or [] if c]
    rubro_clave = normalizar(" ".join(rubros))
    categoria, etiquetas = RUBROS.get(rubro_clave, (None, None))

    if categoria is None:
        es_comida = piso in ("Tercer Piso", "Cuarto Piso")
        categoria = "Gastronomía" if es_comida else "Tienda"
        etiquetas = ",".join(rubros) if rubros else ("comida" if es_comida else "")

    social = tienda.get("social") or {}
    numero = numero_whatsapp(social.get("whatsapp", ""))
    apertura, cierre, ap_dom, ci_dom = HORARIO_POR_PISO.get(piso, ("10:00", "22:00", "11:00", "21:00"))

    lugar = dict(
        nombre=nombre,
        tipo="restaurante" if piso in ("Tercer Piso", "Cuarto Piso") else "tienda",
        categoria=categoria,
        descripcion="",
        piso=piso,
        sector=SECTOR_POR_PISO.get(piso, ""),
        local="",
        referencia="",
        telefono=numero[3:] if numero.startswith("591") else numero,
        whatsapp=f"https://wa.me/{numero}" if numero else "",
        instagram=social.get("instagram") or "",
        facebook=social.get("facebook") or "",
        logo_url=URL + tienda["logo"] if tienda.get("logo") else "",
        hora_apertura=apertura,
        hora_cierre=cierre,
        apertura_domingo=ap_dom,
        cierre_domingo=ci_dom,
        horario_confirmado=False,
        etiquetas=etiquetas,
    )
    lugar.update(AJUSTES.get(nombre, {}))
    if lugar["nombre"] != nombre:
        lugar.update(AJUSTES.get(lugar["nombre"], {}))

    todas = [e.strip() for e in f"{lugar['etiquetas']},{','.join(rubros)}".split(",") if len(e.strip()) > 2]
    lugar["etiquetas"] = ",".join(dict.fromkeys(e.lower() for e in todas))
    if not lugar["descripcion"]:
        lugar["descripcion"] = f"{lugar['categoria']} en el {lugar['piso']} del Paseo Aranjuez."
    return lugar


def main() -> None:
    req = urllib.request.Request(URL + "/stores", headers={"Accept": "application/json"})
    tiendas = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    lugares = [convertir(t) for t in tiendas]

    base = {k: "" for k in ("local", "referencia", "telefono", "whatsapp", "instagram", "facebook", "logo_url")}
    for espacio in ESPACIOS:
        lugares.append({**base, "apertura_domingo": "", "cierre_domingo": "", "hora_apertura": "",
                        "hora_cierre": "", "horario_confirmado": False, **espacio})

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(lugares, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(lugares)} lugares escritos en {DESTINO}")


if __name__ == "__main__":
    main()
