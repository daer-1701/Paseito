"""Canonical FastAPI server for Paseito. All channels share one catalogue and agent."""
import hmac
import json
import os
import re
import sys
from contextlib import asynccontextmanager, closing
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse, FileResponse, StreamingResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'apps' / 'jarvis-backend'))
from .config import FRONTEND_DIR, CORS_ORIGINS
from . import puntos, cupones
from jarvis.bootstrap import load_catalog
from jarvis.store import connect, search, upsert, delete
from jarvis.orchestrator import chat, configured
from jarvis.quality import report
from jarvis import analytics, voice, whatsapp, stimulus
from jarvis.destination import destination_page
from jarvis.qr import destination_qr
from jarvis.conversation import catalog_prices


@asynccontextmanager
async def lifespan(app):
    load_catalog()
    with closing(connect()) as db:
        analytics.schema(db)
        db.commit()
    puntos.iniciar()
    yield


app = FastAPI(title='Paseito API', version='1.0.0', lifespan=lifespan,
              description='Una aplicación, un catálogo, un agente para web y WhatsApp.')
if CORS_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                       allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Content-Type','Authorization','X-Admin-Token'])


@app.exception_handler(ValueError)
async def invalid(request, exc):
    return JSONResponse({'error':str(exc)},status_code=400)


@app.exception_handler(voice.VoiceUnavailable)
async def voice_unavailable(request, exc):
    return JSONResponse({'error':str(exc)},status_code=503)


def admin(request: Request):
    token = os.getenv('JARVIS_INGEST_TOKEN') or os.getenv('ADMIN_TOKEN')
    supplied = request.headers.get('Authorization','').removeprefix('Bearer ') or request.headers.get('X-Admin-Token','')
    if not token or not hmac.compare_digest(token.encode(),supplied.encode()):
        raise HTTPException(401,'Credencial administrativa requerida')


async def body(request, limit=65536):
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit: raise HTTPException(413,'Solicitud demasiado grande')
        chunks.append(chunk)
    return b''.join(chunks)


async def payload(request):
    if request.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
        raise ValueError('Content-Type must be application/json')
    value = json.loads(await body(request))
    if not isinstance(value,dict): raise ValueError('JSON must be an object')
    return value


def with_db(func, *args, **kwargs):
    with closing(connect()) as db:
        return func(db,*args,**kwargs)


@app.get('/health')
@app.get('/salud')
def health():
    with closing(connect()) as db:
        count = db.execute('SELECT COUNT(*) FROM records').fetchone()[0]
    return {'status':'ok','ok':True,'records':count,'application':'Paseito','api':'fastapi',
            'openai_configured':configured(),'ia_configurada':configured(),
            'model':os.getenv('OPENAI_TEXT_MODEL','gpt-4.1-mini'),'fallback':'local',
            'paseo_points':puntos.estado(),'personal_points_enabled':False}


@app.post('/chat')
async def conversation(request: Request):
    data = await payload(request)
    return await run_in_threadpool(with_db,chat,data.get('message') or data.get('mensaje'),data.get('session_id'),channel='web')


@app.get('/cupones/status')
def coupon_status():
    return cupones.status()


@app.post('/cupones/verificar')
async def verify_coupon(request: Request):
    import time
    start = time.monotonic()
    data = await payload(request)
    session = data.get('session_id')
    if not isinstance(session,str) or not 1<=len(session)<=100:
        raise ValueError('session_id requerido')
    result = await run_in_threadpool(cupones.verificar, data.get('codigo'))
    with closing(connect()) as db:
        venues = search(db,'',kinds={'venue'},browse=True,limit=1000)
        from jarvis.store import tokens
        for card in result.get('resultados',[]):
            name = tokens(card.get('nombre',''))
            matches = [v for v in venues if tokens(v['title'])==name or (name and name<tokens(v['title']))]
            if len(matches)==1:
                v=matches[0]; a=v['attributes']
                card['venue_id']=v['id']
                card['ubicacion']={'piso':a.get('floor',''),'local':a.get('unit',''),'sector':a.get('area','')}
                card['fuente_url']='/catalog/demo' if result.get('demo') else v['source_url']
                card['foto']=a.get('image_url','')
        # No QR, customer identifiers or coupon codes in persisted analytics.
        analytics.record(db,'Consulta de cupones mediante lector',
            {'session_id':session,'tarjetas':result.get('resultados',[]),
             'intent':'loyalty','answer_mode':'coupon_demo' if result.get('demo') else 'points_coupon'},
            'web',round((time.monotonic()-start)*1000),
            [{'nombre':'verificar_cupon','argumentos':{},'resultados':len(result.get('resultados',[]))}],
            'points_unavailable' if result.get('error') else None)
    return JSONResponse(result,headers={'Cache-Control':'no-store'})


@app.delete('/chat/{session_id}')
def reset(session_id: str):
    if not 1 <= len(session_id) <= 100: raise ValueError('invalid session_id')
    with closing(connect()) as db:
        for table in ('turns','session_context','session_preferences'):
            db.execute(f'DELETE FROM {table} WHERE session_id=?',(session_id,))
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='stimulus_welcome'").fetchone():
            db.execute('DELETE FROM stimulus_welcome WHERE session_id=?',(session_id,))
        db.commit()
    return {'deleted':True}


@app.get('/catalog')
def catalog(kind: str=Query('venue',pattern='^(venue|product|promotion|event|faq)$'),q: str='',limit: int=Query(50,ge=1,le=200),tienda: str|None=None):
    def read(db):
        rows = search(db,q,kinds={kind},browse=not q.strip(),limit=limit,venue_ids={tienda} if tienda else None)
        return catalog_prices(db,rows) if kind=='product' else rows
    return with_db(read)


def catalog_endpoint(kind):
    def endpoint(q: str='',limit: int=Query(50,ge=1,le=200)):
        return catalog(kind,q,limit)
    return endpoint


for url,kind in [('/lugares','venue'),('/productos','product'),('/promociones','promotion'),('/eventos','event'),('/faqs','faq')]:
    app.add_api_route(url,catalog_endpoint(kind),methods=['GET'],include_in_schema=False)


@app.get('/kiosk/config')
def kiosk_config():
    return {'origin':os.getenv('JARVIS_KIOSK_ORIGIN','Punto del kiosco pendiente de configurar'),
            'public_base_url':os.getenv('JARVIS_MOBILE_BASE_URL',''),
            'demo_catalog':os.getenv('JARVIS_DEMO_CATALOG')=='1',
            'stimulus_enabled':os.getenv('JARVIS_STIMULUS_ENABLED')=='1'}


@app.get('/destination/{record_id}')
def destination(record_id: str):
    page = with_db(destination_page,record_id)
    if page is None: raise HTTPException(404,'Destino no disponible')
    return HTMLResponse(page,headers={'Cache-Control':'no-store'})


@app.get('/qr/destination/{record_id}')
def qr(record_id: str):
    svg = with_db(destination_qr,record_id)
    if svg is None: raise HTTPException(404,'QR no disponible')
    return Response(svg,media_type='image/svg+xml',headers={'Cache-Control':'no-store'})


@app.get('/catalog/demo')
def demo_info():
    return HTMLResponse('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Modo demo</title><main style="font:18px/1.6 system-ui;max-width:650px;margin:40px auto;padding:20px"><h1>Modo demo</h1><p>El catálogo, sus precios, promociones, Points público sin conexión externa y los horarios que faltaban son datos de demostración. No constituyen inventario confirmado ni ofertas oficiales. Los horarios reales documentados se conservan. Los negocios y ubicaciones provienen de las fuentes citadas en sus fichas.</p><a href="/">Volver a Paseito</a></main></html>')


@app.get('/voice/status')
def voice_status():
    return voice.status()


@app.post('/voice/transcribe')
async def transcribe(request: Request):
    data = await body(request,voice.MAX_AUDIO_BYTES)
    return {'text':await run_in_threadpool(voice.transcribe,data)}


@app.post('/voice/synthesize')
async def synthesize(request: Request):
    data = await payload(request)
    audio,mime = await run_in_threadpool(voice.synthesize,data.get('text'))
    return Response(audio,media_type=mime,headers={'Cache-Control':'no-store'})


@app.post('/voice/stream')
async def stream(request: Request):
    data = await payload(request)
    generator = voice.stream_speech(data.get('text'))
    try:
        first = await run_in_threadpool(lambda: next(generator,None))
        if not first: raise voice.VoiceUnavailable('empty speech stream')
    except Exception:
        generator.close()
        raise
    async def chunks():
        try:
            current = first
            while current is not None:
                yield current
                current = await run_in_threadpool(lambda: next(generator,None))
        finally:
            generator.close()
    return StreamingResponse(chunks(),media_type='application/x-ndjson',
                             headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})


@app.get('/whatsapp/status')
def whatsapp_status():
    return whatsapp.config_status()


@app.get('/whatsapp/demo')
def whatsapp_demo():
    if os.getenv('JARVIS_DEMO_CATALOG')!='1': raise HTTPException(404,'Demo deshabilitada')
    return FileResponse(FRONTEND_DIR/'whatsapp.html')


@app.post('/whatsapp/demo/message')
async def whatsapp_message(request: Request):
    if os.getenv('JARVIS_DEMO_CATALOG')!='1': raise HTTPException(404,'Demo deshabilitada')
    data = await payload(request)
    identity = data.get('session_id','')
    if not isinstance(identity,str) or not re.fullmatch(r'[a-zA-Z0-9-]{8,80}',identity): raise ValueError('invalid demo session')
    result = await run_in_threadpool(whatsapp.incoming,identity,data.get('message_id'),data.get('message'),'local_demo')
    return {'answer':result['channel_answer'],'suggestions':result.get('suggestions',[]),'duplicate':result['duplicate'],'local_only':True}


@app.post('/whatsapp/webhook')
async def webhook(request: Request):
    try:
        sender,sid,message = whatsapp.validate_twilio(await body(request),request.headers.get('X-Twilio-Signature'),request.url.path)
        result = await run_in_threadpool(whatsapp.incoming,sender,sid,message)
        return Response(whatsapp.twiml(result),media_type='application/xml')
    except PermissionError: raise HTTPException(403,'Firma inválida') from None
    except RuntimeError: raise HTTPException(503,'Conector no configurado') from None


@app.post('/stimulus/gaze')
async def gaze(request: Request):
    data = await payload(request)
    for key in ('welcome','busy','manual'):
        if key in data and not isinstance(data[key],bool): raise ValueError(f'{key} must be boolean')
    def invoke(db):
        result = stimulus.gaze(db,data.get('session_id'),data.get('target_id'),data.get('dwell_ms'),
                              welcome=data.get('welcome',False),busy=data.get('busy',True),manual=data.get('manual',False))
        if result.get('triggered'):
            analytics.record(db,'saludo_mirada',result['chat'],'stimulus_demo' if data.get('manual') else 'stimulus',0,
                             [{'nombre':'saludo_mirada','argumentos':{},'resultados':0}])
        return result
    return await run_in_threadpool(with_db,invoke)


@app.get('/points/programa')
def points_program(tema: str='todo'):
    return puntos.programa_puntos(None,tema)


@app.get('/points/personal')
def points_personal():
    raise HTTPException(403,'Identidad verificada pendiente. Consulta personal deshabilitada.')


@app.get('/admin/quality',dependencies=[Depends(admin)])
def quality():
    return with_db(report)


@app.get('/admin/records',dependencies=[Depends(admin)])
def records(q: str='',limit: int=Query(100,ge=1,le=200),offset: int=Query(0,ge=0)):
    with closing(connect()) as db:
        rows = db.execute('SELECT * FROM records WHERE title LIKE ? ORDER BY kind,title LIMIT ? OFFSET ?',('%'+q+'%',limit,offset)).fetchall()
        return [{**dict(r),'attributes':json.loads(r['attributes'])} for r in rows]


@app.post('/admin/records',dependencies=[Depends(admin)])
async def save(request: Request):
    data = await payload(request)
    def write(db):
        if data.get('kind') in {'product','promotion'} and not db.execute("SELECT 1 FROM records WHERE id=? AND kind='venue'",(data.get('attributes',{}).get('venue_id'),)).fetchone():
            raise ValueError('unknown venue_id')
        upsert(db,data,restore=True)
        return {'id':data['id'],'status':'upserted'}
    return await run_in_threadpool(with_db,write)


@app.delete('/admin/records/{record_id}',dependencies=[Depends(admin)])
def remove(record_id: str):
    def write(db):
        if db.execute("SELECT kind FROM records WHERE id=?",(record_id,)).fetchone() and any(json.loads(r[0]).get('venue_id')==record_id for r in db.execute("SELECT attributes FROM records WHERE kind IN ('product','promotion')")):
            raise ValueError('Venue has linked products or promotions; remove them first')
        return delete(db,record_id)
    found = with_db(write)
    if not found: raise HTTPException(404,'Registro no encontrado')
    return {'id':record_id,'deleted':True}


@app.get('/analitica/resumen',dependencies=[Depends(admin)])
def metrics(top: int=Query(10,ge=1,le=50)):
    return with_db(analytics.summary,top)


@app.get('/analitica/consultas',dependencies=[Depends(admin)])
def queries(limite: int=Query(50,ge=1,le=200)):
    with closing(connect()) as db:
        analytics.schema(db)
        return [{**dict(r),'herramientas':json.loads(r['herramientas'])} for r in db.execute('SELECT * FROM consultas ORDER BY id DESC LIMIT ?',(limite,))]


@app.get('/kiosco',include_in_schema=False)
@app.get('/kiosk',include_in_schema=False)
def kiosk(): return RedirectResponse('/')


class FrontendSinCache(StaticFiles):
    async def get_response(self,path,scope):
        response = await super().get_response(path,scope)
        response.headers['Cache-Control']='no-cache'
        return response


if FRONTEND_DIR.is_dir():
    # Asset compatibility only; both URLs serve the very same files.
    app.mount('/kiosk',FrontendSinCache(directory=FRONTEND_DIR),name='kiosk-assets')
    app.mount('/',FrontendSinCache(directory=FRONTEND_DIR,html=True),name='frontend')


def run():
    import uvicorn
    uvicorn.run('app.main:app',host=os.getenv('JARVIS_HOST','127.0.0.1'),port=int(os.getenv('JARVIS_PORT','8000')),workers=1)


if __name__=='__main__': run()
