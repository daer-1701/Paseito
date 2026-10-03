"""Generate explicitly synthetic, priced catalogues for the hackathon demonstration."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
STAMP = datetime.now(timezone.utc).isoformat()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/jarvis-backend'))
from jarvis.import_official import normalized

# Amounts are authored estimates in BOB, not scraped or approved selling prices.
profiles = {
'entretenimiento': [(f'{activity} · {duration} minutos',price) for activity in ('Zona de juegos infantil','Juego interactivo','Circuito infantil','Diversión familiar','Sala de juegos') for duration,price in ((15,20),(30,35),(45,50),(60,65),(90,90))],
'salon': [('Corte de cabello',70),('Lavado y peinado',55),('Brushing',80),('Peinado sencillo',100),('Peinado de fiesta',180),('Coloración raíz',180),('Coloración completa',280),('Mechas',350),('Tratamiento hidratante',120),('Tratamiento capilar',160),('Corte infantil',45),('Corte caballero',55),('Barba',35),('Manicura clásica',45),('Manicura gel',85),('Pedicura clásica',65),('Pedicura gel',100),('Retiro de esmalte gel',30),('Decoración de uñas',25),('Fortalecimiento de uñas',95),('Uñas acrílicas',160),('Retoque de uñas',110),('Maquillaje social',180),('Perfilado de cejas',35),('Depilación facial',40)],
'artesania': [('Bolso tejido',160),('Monedero tejido',45),('Bufanda artesanal',110),('Chal tejido',190),('Manta de lana',250),('Gorro tejido',65),('Guantes tejidos',55),('Cojín artesanal',90),('Tapiz pequeño',140),('Tapiz mediano',230),('Canasta pequeña',65),('Canasta mediana',110),('Portavasos tejido',25),('Camino de mesa',130),('Individual tejido',35),('Collar artesanal',75),('Pulsera artesanal',30),('Aretes artesanales',45),('Llavero tejido',20),('Muñeco tejido',90),('Portarretrato artesanal',60),('Florero cerámico',120),('Taza cerámica',45),('Plato cerámico',55),('Set regalo artesanal',180)],
'ropa': [('Camisa de algodón',150),('Camisa manga corta',120),('Camisa formal',220),('Camisa de lino',260),('Polera básica',75),('Polera estampada',95),('Polo clásico',140),('Blusa casual',130),('Blusa formal',180),('Jeans clásico',230),('Jeans recto',250),('Pantalón formal',270),('Pantalón deportivo',160),('Short de algodón',110),('Falda casual',150),('Vestido casual',240),('Vestido de fiesta',450),('Sudadera',210),('Buzo con capucha',240),('Chaqueta ligera',320),('Chompa tejida',230),('Abrigo',580),('Conjunto deportivo',350),('Cinturón',90),('Gorra',85)],
'infantil': [('Polera infantil',65),('Camisa infantil',110),('Jeans infantil',150),('Pantalón infantil',120),('Short infantil',75),('Vestido infantil',160),('Conjunto bebé',110),('Body bebé',55),('Pack bodies bebé',145),('Pijama infantil',100),('Sudadera infantil',140),('Chaqueta infantil',210),('Abrigo infantil',280),('Chompa infantil',135),('Calcetines infantiles',20),('Gorro bebé',35),('Babero',25),('Manta bebé',90),('Pantalón bebé',55),('Enterizo bebé',95),('Leggings infantiles',65),('Falda infantil',90),('Conjunto deportivo infantil',185),('Zapatillas infantiles',220),('Sandalias infantiles',95)],
'juguetes': [('Rompecabezas infantil',45),('Bloques de construcción',90),('Auto de juguete',35),('Muñeca básica',85),('Pelota infantil',30),('Peluche pequeño',55),('Peluche grande',160),('Juego de mesa familiar',120),('Juego de cartas',35),('Set de plastilina',40),('Kit de dibujo infantil',65),('Set de pintura infantil',75),('Libro para colorear',25),('Cubo Rubik',35),('Tren de madera',140),('Cocina de juguete',350),('Casa de muñecas',480),('Auto control remoto',240),('Robot de juguete',190),('Dinosaurio de juguete',80),('Instrumento musical infantil',90),('Kit de ciencia infantil',150),('Pista de autos',280),('Figura coleccionable',170),('Juguete sensorial bebé',60)],
'calzado': [('Zapatillas casuales',290),('Zapatillas deportivas',380),('Zapatillas para correr',520),('Zapato formal',350),('Mocasines',320),('Botines',420),('Botas',580),('Sandalias',180),('Sandalias deportivas',240),('Chinelas',80),('Zuecos casuales',280),('Zuecos infantiles',190),('Zapatillas infantiles',220),('Zapatos escolares',200),('Ballerinas',160),('Alpargatas',150),('Tacones clásicos',280),('Sandalias de tacón',300),('Botas de lluvia',230),('Zapato de trabajo',310),('Zapatillas urbanas',340),('Plantillas',45),('Cordones',20),('Medias deportivas',35),('Limpiador de calzado',60)],
'tecnologia': [('Cable USB-C',45),('Cargador rápido',120),('Auriculares con cable',70),('Auriculares Bluetooth',220),('Parlante portátil',250),('Power bank',180),('Funda para celular',55),('Protector de pantalla',35),('Soporte para celular',45),('Mouse inalámbrico',90),('Teclado inalámbrico',150),('Webcam',210),('Memoria USB 64 GB',70),('Tarjeta microSD 128 GB',110),('Adaptador HDMI',85),('Hub USB',130),('Smartwatch básico',390),('Pulsera inteligente',230),('Celular de entrada',1100),('Celular gama media',2200),('Celular gama alta',5200),('Tablet básica',1350),('Tablet gama media',2200),('Audífonos gaming',240),('Control de videojuegos',280)],
'belleza': [('Labial',55),('Brillo labial',35),('Base de maquillaje',110),('Corrector',65),('Polvo compacto',75),('Rubor',60),('Máscara de pestañas',70),('Delineador',35),('Paleta de sombras',140),('Brochas de maquillaje',120),('Esponja de maquillaje',25),('Desmaquillante',55),('Limpiador facial',85),('Crema hidratante',110),('Protector solar',150),('Champú',70),('Acondicionador',65),('Mascarilla capilar',95),('Aceite capilar',85),('Esmalte de uñas',25),('Kit de manicura',60),('Crema de manos',40),('Perfume pequeño',180),('Peine profesional',35),('Cepillo para cabello',50)],
'accesorios': [('Mochila urbana',240),('Mochila escolar',190),('Mochila laptop',320),('Bolso pequeño',140),('Bolso de mano',210),('Cartera',180),('Billetera',95),('Monedero',45),('Riñonera',90),('Maleta pequeña',450),('Maleta mediana',650),('Maleta grande',850),('Cartuchera',45),('Neceser',65),('Gorra',85),('Sombrero',120),('Bufanda',75),('Guantes',50),('Cinturón',90),('Llavero',25),('Gafas de sol',180),('Reloj casual',260),('Pulsera',55),('Collar',90),('Aretes',60)],
'lenceria': [('Brasier básico',85),('Brasier deportivo',110),('Brasier encaje',120),('Top interior',65),('Body',160),('Camiseta interior',60),('Calzón básico',30),('Pack calzones',85),('Bóxer',45),('Pack bóxers',120),('Pijama algodón',150),('Pijama satén',210),('Camisón',140),('Bata',220),('Short pijama',70),('Medias básicas',20),('Pack medias',55),('Medias térmicas',45),('Leggings',120),('Panty',35),('Panty térmica',65),('Traje de baño',240),('Bikini',210),('Salida de baño',110),('Conjunto interior',190)],
'hogar': [('Taza de cerámica',40),('Vaso',25),('Set vasos',120),('Plato',35),('Set platos',210),('Cubiertos',95),('Botella térmica',110),('Termo',160),('Sartén',140),('Olla',180),('Tabla de cocina',65),('Organizador',75),('Cojín',70),('Manta',120),('Toalla',65),('Sábana',180),('Lámpara de mesa',160),('Reloj de pared',120),('Florero',80),('Vela aromática',55),('Difusor',90),('Cuadro decorativo',140),('Portarretrato',45),('Maceta',60),('Espejo',190)],
'joyas': [('Aretes acero',90),('Aretes plata',220),('Aretes pequeños',65),('Argollas',130),('Collar acero',140),('Collar plata',320),('Collar dije',180),('Cadena fina',210),('Pulsera acero',110),('Pulsera plata',260),('Pulsera tejida',45),('Anillo acero',85),('Anillo plata',190),('Anillo con piedra',240),('Dije',95),('Tobillera',75),('Broche',90),('Set collar y aretes',280),('Set pulseras',160),('Reloj casual',350),('Reloj clásico',550),('Joyero pequeño',90),('Joyero de viaje',130),('Cadena para lentes',55),('Pendientes largos',150)],
'perfumes': [(f'Perfume {style} {size} ml',price) for style in ('floral','cítrico','amaderado','fresco','oriental') for size,price in ((10,55),(30,140),(50,220),(75,310),(100,390))],
'medias': [(f'Medias {style} · {pack}',price) for style in ('básicas','deportivas','estampadas','infantiles','térmicas') for pack,price in (('par',25),('pack 2 pares',45),('pack 3 pares',65),('pack 5 pares',100),('pack regalo',85))],
'flores': [(f'{flower} · {size}',price) for flower in ('Ramo de rosas','Ramo de flores mixtas','Arreglo de girasoles','Arreglo floral','Ramo de tulipanes') for size,price in (('pequeño',80),('mediano',150),('grande',240),('con tarjeta',170),('con jarrón',260))],
'optica': [(f'{item} · {style}',price) for item,price in (('Montura',180),('Gafas de sol',220),('Estuche de lentes',45),('Paño de limpieza',15),('Cordón para lentes',25)) for style in ('clásico','moderno','deportivo','infantil','compacto')],
}
menus = {
'turca': [('Kebab de pollo',35),('Kebab de carne',42),('Döner en pan',40),('Dürüm',45),('Falafel',30),('Hummus con pan',28),('Plato mixto',55),('Ensalada',25),('Limonada',18),('Gaseosa',12)],
'pizza': [('Pizza margarita personal',45),('Pizza pepperoni personal',50),('Pizza vegetariana personal',48),('Pizza cuatro quesos',65),('Pizza familiar',110),('Calzone',50),('Pan de ajo',25),('Ensalada mixta',35),('Limonada',18),('Gaseosa',12)],
'hamburguesa': [('Hamburguesa clásica',35),('Hamburguesa con queso',40),('Hamburguesa doble',55),('Hamburguesa de pollo',38),('Hamburguesa vegetariana',40),('Lomito',45),('Papas fritas',18),('Combo hamburguesa y bebida',50),('Limonada',18),('Gaseosa',12)],
'cafe': [('Café espresso',15),('Café americano',18),('Capuchino',24),('Latte',25),('Chocolate caliente',24),('Té',15),('Sándwich de pollo',30),('Sándwich vegetariano',28),('Brownie',20),('Porción de torta',25)],
'postres': [('Helado una porción',15),('Helado dos porciones',25),('Copa de helado',35),('Waffle con frutas',35),('Waffle con chocolate',32),('Brownie con helado',38),('Churros clásicos',20),('Churros rellenos',28),('Batido de frutas',25),('Café americano',18)],
'pasta': [('Pasta boloñesa',48),('Pasta Alfredo',48),('Pasta al pesto',50),('Pasta vegetariana',45),('Lasaña',55),('Ravioles',58),('Ensalada',32),('Pan de ajo',22),('Limonada',18),('Gaseosa',12)],
'mexicana': [('Tacos de pollo',35),('Tacos de carne',40),('Burrito de pollo',45),('Burrito vegetariano',40),('Quesadilla',35),('Nachos con queso',30),('Nachos completos',45),('Guacamole',22),('Limonada',18),('Gaseosa',12)],
'japonesa': [('Roll de sushi clásico',50),('Roll vegetariano',45),('Roll tempura',58),('Combo sushi 16 piezas',95),('Ramen',55),('Yakimeshi',42),('Gyozas',35),('Ensalada',30),('Té frío',18),('Limonada',18)],
'criolla': [('Pique macho personal',55),('Silpancho',40),('Milanesa con papas',45),('Brocheta de carne',45),('Brocheta de pollo',40),('Charque personal',65),('Chorizo con acompañamiento',35),('Ensalada',25),('Mocochinchi',15),('Limonada',18)],
'espanola': [('Tortilla española',38),('Croquetas',35),('Patatas bravas',30),('Paella personal',65),('Bocadillo de jamón',45),('Tabla de quesos',75),('Gazpacho',28),('Ensalada',32),('Limonada',18),('Gaseosa',12)],
'bar': [('Hamburguesa de la casa',45),('Tabla para compartir',95),('Nachos',35),('Pique personal',60),('Ensalada',35),('Brownie',22),('Limonada',20),('Mocktail de frutas',28),('Cóctel clásico',40),('Cerveza artesanal',30)],
}
venues = json.loads((ROOT/'docs/entregables/datos-paseo/negocios-para-revision.json').read_text(encoding='utf-8-sig'))
aliases = {'almacendepizzas':'pizza','bypassburger':'hamburguesa','lasangucheriacafe':'hamburguesa','chipotlemexicanfood':'mexicana','chottomatte':'japonesa','delistambul':'turca','parrilleros':'criolla','hoyhay':'criolla','pawitos':'cafe','vacafria':'postres','heladosvacafria':'postres','yummycandybar':'postres','cinnabon':'postres','cayenna':'bar','elcuartobypaseo':'bar','monalisabierhaus':'bar'}
records, coverage = [], []
for venue in venues:
    a, title = venue['attributes'], venue['title']
    key, category = normalized(title), normalized(a.get('category',''))
    if venue['id'] in {'venue:century-21-cochabamba','venue:minerva-montero'}:
        coverage.append({'venue_id':venue['id'],'title':title,'count':0,'reason':'Oficina o consultorio: no inventar catálogo minorista.'})
        continue
    group = aliases.get(key)
    if 'patanegra' in key: group='espanola'
    if not group:
        for term, candidate in [('pizza','pizza'),('pasta','pasta'),('churro','postres'),('waffle','postres'),('helado','postres'),('postre','postres'),('brocheta','criolla'),('charque','criolla'),('espanola','espanola'),('italiana','pasta'),('gastronomia','bar')]:
            if term in category or term in key: group=candidate; break
    if group:
        items=menus[group]
    else:
        group='accesorios'
        for term,candidate in [('infantil','infantil'),('bebe','infantil'),('juguet','juguetes'),('games','juguetes'),('gameshop','juguetes'),('jeans','ropa'),('ropa','ropa'),('boutique','ropa'),('calzado','calzado'),('deporte','ropa'),('fitness','ropa'),('lencer','lenceria'),('tecnolog','tecnologia'),('phone','tecnologia'),('telecom','tecnologia'),('cosmet','belleza'),('belleza','belleza'),('personal','belleza'),('perfumer','perfumes'),('joy','joyas'),('reloj','joyas'),('medias','medias'),('florister','flores'),('hogar','hogar'),('optic','optica')]:
            if term in category or term in key: group=candidate; break
        if 'lencer' in category: group='lenceria'
        if key == 'skygames': group='entretenimiento'
        if key in {'rezzombeauty','nailsexpressgel'}: group='salon'
        if 'artesania' in category: group='artesania'
        items=profiles[group]
    coverage.append({'venue_id':venue['id'],'title':title,'profile':group,'count':len(items)})
    for index,(name,price) in enumerate(items,1):
        records.append({'id':f"product:demo:{venue['id'].removeprefix('venue:')}:{index:02}",'kind':'product',
                        'title':f'{name} · {title}','text':f'{name}. {group}. {title}. Catálogo ficticio de demostración; regalo y presupuesto.',
                        'source_url':'http://localhost:8000/catalog/demo','updated_at':STAMP,
                        'attributes':{'venue_id':venue['id'],'venue_name':title,'category':group,'description':f'{name}, ejemplo para demostrar búsqueda y precios.',
                                      'price_bs':price,'data_origin':'synthetic_demo','source_type':'demo_catalog','review_status':'sourced',
                                      'price_scope':'estimated_demo','reference':'Producto y precio simulados. No es oferta del negocio ni confirma disponibilidad.'}})
out=ROOT/'apps/jarvis-backend/data/demo-catalog.json'
out.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'docs/entregables/catalogo-demo-cobertura.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'products':len(records),'venues_with_catalog':sum(r['count']>0 for r in coverage),'excluded':sum(r['count']==0 for r in coverage)},ensure_ascii=False))
