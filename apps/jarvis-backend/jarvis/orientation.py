"""Conversational spatial context derived exclusively from directory fields."""


def location_text(attributes):
    parts=[]
    floor=str(attributes.get('floor') or '').strip()
    if floor:
        parts.append(floor.lower() if any(w in floor.lower() for w in ('piso','planta','sótano','sotano')) else f'piso {floor}')
    for field,label in (('area','sector'),('tower','torre'),('unit','local')):
        value=str(attributes.get(field) or '').strip()
        if value:
            parts.append(value if value.lower().startswith(('oficina ',label+' ')) else f'{label} {value}')
    text=', '.join(parts)
    reference=attributes.get('reference')
    if reference and attributes.get('data_origin')!='synthetic_demo':
        text+=f'. Como referencia: {reference}'
    return text
