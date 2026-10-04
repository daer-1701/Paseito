# Etapa 2 aprobada: identidad temporal, Points y orientación

Base: `114c0c5`. El usuario aprobó implementar las correcciones tras revisar la primera etapa.

## Contratos

- Una identidad Points obtenida mediante QR validado. Credencial aleatoria HttpOnly/SameSite ligada a conversación; no basta conocer session_id, teléfono o correo.
- 90 segundos sin actividad conversacional y máximo 10 minutos. Reinicio/cierre revocan. Estado personal solo en memoria del servidor y pantalla; no SQLite, analytics ni historial OpenAI. Una instancia/worker, como el despliegue actual.
- Un código de cupón consulta solo ese cupón; los demás se consultan mediante QR de cliente o web de Points.
- API QR por HTTPS fuera de loopback, sin redirecciones; HMAC dedicado, firma y vencimiento válidos. Un intento y mensaje de alternativa web.
- Points mantiene TLS verificado, caché pública 300 s, máximo 600 s, filtrado de vigencia y refresco en segundo plano. No caché de saldos personales ni reintentos bloqueantes.
- Ubicación conversacional basada en piso/sector/local y referencias publicadas. Sin distancias, ascensores o tiempos inventados. Integrar contexto de orientación en chat, tarjetas y ficha pública.
- Catálogo existente con fuentes; conflictos comerciales requieren revisión administrativa. Token administrativo siempre obligatorio. OpenAI + respaldo local permanecen.

## Implementación

1. Añadir gestor de identidad temporal y endurecer validación QR.
2. Consulta personal de solo lectura y endpoints con cookie, vencimiento y revocación. Separar respuesta personal del LLM/historial.
3. Frontend: saldo/puntos, indicador temporal, actividad limitada, borrado y cierre por inactividad/cambio de conversación. Demo de identidad explícita para revisión sin credenciales.
4. Orientación factual y contexto espacial; mensajes de un intento/alternativa web.
5. Build y recorridos manuales; no añadir ni ejecutar suites automatizadas. Revisión final de código, commit y rama publicada.

## Límites conocidos

Credenciales reales de Points y OpenAI no configuradas en la torre. La demo temporal permite revisar el flujo sin acreditar saldo real. Sesión temporal en memoria se invalida si el proceso se reinicia. Despliegues con múltiples workers necesitan coordinación de revocación.

## Registro de ejecución

Pasos 1–4 implementados. Paso 5: tres builds correctos, recorridos manuales API/browser, caducidad real tras 92 segundos y revisión final de código completados. Evidencia detallada en docs/entregables/etapa2-points-sesion.md.

La instrucción del desarrollador de no añadir ni ejecutar tests sin solicitud prevalece sobre el ciclo TDD de la skill: no se ejecutaron suites. Se realizó una sola revisión final por un agente de solo lectura, conforme a executing-plans. Se corrigieron sus tres hallazgos: voz privada externa/caché, límite absoluto para cupón sin identidad y renovación por actividad general. También se evita borrar cookies nuevas con respuestas tardías de logout, se cancela lectura QR en vuelo al cerrar y se aborta chat pendiente al terminar el permiso. Ningún hallazgo importante permanece abierto en esa revisión. Integración real externa y múltiples workers quedan explícitamente fuera del despliegue actual.
