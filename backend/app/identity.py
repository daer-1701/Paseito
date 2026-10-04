"""Ephemeral browser capability for a QR-verified Points conversation.

No identity or balance is persisted. A cookie alone or session_id alone is insufficient.
"""
import hashlib
import secrets
import threading
import time

COOKIE='paseito_points'
IDLE_SECONDS=90
MAX_SECONDS=600
_lock=threading.Lock()
_grants={}
_attempts={}


def _key(token):
    return hashlib.sha256((token or '').encode()).hexdigest()


def _prune(now):
    for key, grant in list(_grants.items()):
        if now>=grant['idle_until'] or now>=grant['hard_until']:del _grants[key]
    for sid, attempt in list(_attempts.items()):
        if now-attempt[1]>MAX_SECONDS:del _attempts[sid]


def _cancel(session):
    # Unknown sessions have no in-flight read to cancel. Keep the map bounded.
    if session in _attempts:
        _attempts[session]=(secrets.token_hex(16),time.monotonic())


def begin(session):
    now=time.monotonic()
    with _lock:
        _prune(now)
        if len(_attempts)>=4096 and session not in _attempts:
            raise ValueError('Demasiadas conversaciones; intenta de nuevo más tarde.')
        ticket=secrets.token_hex(16)
        _attempts[session]=(ticket,now)
        for key, grant in list(_grants.items()):
            if grant['session_id']==session:del _grants[key]
        return ticket


def issue(session, ticket, user=None, demo=False):
    now=time.monotonic()
    with _lock:
        _prune(now)
        if _attempts.get(session,(None,))[0]!=ticket:return None
        if len(_grants)>=4096:raise ValueError('Demasiadas conversaciones; intenta nuevamente.')
        token=secrets.token_urlsafe(32)
        _grants[_key(token)]={'session_id':session,'user_id':user,'demo':demo,
            'idle_until':now+IDLE_SECONDS,'hard_until':now+MAX_SECONDS,'grant_id':ticket}
        return token


def current(session,ticket):
    with _lock:
        _prune(time.monotonic())
        return _attempts.get(session,(None,))[0]==ticket


def get(token, session, touch=False):
    now=time.monotonic()
    with _lock:
        _prune(now)
        grant=_grants.get(_key(token))
        if not grant or grant['session_id']!=session:return None
        if touch:grant['idle_until']=min(grant['hard_until'],now+IDLE_SECONDS)
        return dict(grant)


def public(grant):
    if not grant:return {'authenticated':False,'idle_seconds':IDLE_SECONDS}
    now=time.monotonic()
    return {'authenticated':True,'demo':grant['demo'],'idle_seconds':IDLE_SECONDS,
        'expires_in_ms':max(0,int((min(grant['idle_until'],grant['hard_until'])-now)*1000)),
        'hard_expires_in_ms':max(0,int((grant['hard_until']-now)*1000))}


def revoke(token, session):
    with _lock:
        _prune(time.monotonic())
        grant=_grants.get(_key(token))
        if grant and grant['session_id']==session:del _grants[_key(token)]
        # Cancels in-flight QR validation for this same conversation.
        _cancel(session)


def revoke_session(session):
    with _lock:
        _prune(time.monotonic())
        for key,grant in list(_grants.items()):
            if grant['session_id']==session:del _grants[key]
        _cancel(session)
