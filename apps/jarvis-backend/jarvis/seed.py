"""Small clearly fictional catalog for local integration tests."""

from datetime import datetime, timezone

from .store import connect, upsert


DEMO = [
    {"id": "venue:demo-cafe", "kind": "venue", "title": "Café Demo",
     "text": "Cafetería de demostración con bebidas calientes, postres y opciones rápidas. Datos ficticios para probar Jarvis.",
     "attributes": {"floor": "2", "unit": "Demo 201", "category": "café"}},
    {"id": "venue:demo-regalos", "kind": "venue", "title": "Regalos Demo",
     "text": "Tienda de demostración con regalos y accesorios. Datos ficticios para probar Jarvis.",
     "attributes": {"floor": "1", "unit": "Demo 102", "category": "regalos"}},
    {"id": "product:demo-taza", "kind": "product", "title": "Taza de regalo Demo",
     "text": "Producto ficticio de Regalos Demo para probar la búsqueda. Precio y disponibilidad no confirmados.",
     "attributes": {"venue_id": "venue:demo-regalos", "category": "regalos"}},
]


def main() -> None:
    updated = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        for record in DEMO:
            upsert(db, {**record, "updated_at": updated})
    print(f"Loaded {len(DEMO)} fictional demonstration records")


if __name__ == "__main__":
    main()
