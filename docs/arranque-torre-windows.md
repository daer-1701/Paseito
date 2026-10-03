# Jarvis local en Windows 11 + WSL2 + RTX 4070

Esta torre ejecuta la misma aplicación FastAPI y frontend responsive descritos en
[arranque del equipo](arranque-equipo.md). OpenAI es el proveedor principal cuando
se configura la clave en el `.env` raíz; sin clave funciona el respaldo local.
La voz usa faster-whisper y Kokoro en CUDA. Los datos y sesiones son únicos.

## Preparación de Windows — una sola vez

1. Instalar o actualizar el controlador NVIDIA **en Windows**. NVIDIA indica que
   no se debe instalar un controlador de pantalla Linux dentro de WSL.
2. Instalar Ubuntu en WSL2 y actualizarlo desde PowerShell:

   ```powershell
   wsl --install -d Ubuntu
   wsl --update
   wsl --list --verbose
   ```

   Ubuntu debe figurar como versión 2. Reiniciar si Windows lo solicita.
3. Instalar Docker Desktop; activar **Use the WSL 2 based engine** y la
   integración de Ubuntu en **Resources → WSL Integration**. Usar contenedores
   Linux. Abrir Docker Desktop antes de arrancar Jarvis.
4. En Ubuntu, comprobar `docker compose version` y `nvidia-smi`. Reservar espacio
   para imágenes CUDA y modelos: recomendamos al menos 20 GB libres. Si WSL se
   queda sin memoria durante el build, revisar su límite de RAM; la torre tiene
   32 GB compartidos con Windows.

Fuentes: [Docker Desktop y GPU en WSL2](https://docs.docker.com/desktop/features/gpu/),
[NVIDIA CUDA en WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

## Clonar y arrancar — terminal Ubuntu WSL

Clonar en el filesystem de Linux, por ejemplo `~/Developer`, para evitar el
coste de acceso a archivos de `/mnt/c`. Sustituir la URL por la del monorepo:

```bash
git clone --branch feat/version-unica-openai https://github.com/daer-1701/Paseito.git paseo-aranjuez-digital
cd paseo-aranjuez-digital
bash scripts/start-tower.sh
```

El script genera `.env` con un secreto aleatorio de ingesta, verifica CUDA dentro
de Docker, construye las imágenes, descarga los modelos a un volumen persistente,
los carga y prueba antes de marcar el servicio como disponible. El primer arranque
requiere Internet y puede tardar varios minutos. Espera hasta 30 minutos; si
expira, revisar los logs y repetir, conservando las descargas previas.

Abrir **http://localhost:8000 en Chrome o Edge de Windows**. Pulsar la bienvenida,
permitir micrófono y consultar por un café. El navegador usa la transcripción de
la torre; no selecciona el reconocimiento remoto del navegador en este perfil.

La rama ya está publicada en Paseito. Para equipos sin NVIDIA, seguir la
[guía del equipo](arranque-equipo.md). Para mostrar catálogo, horarios de demo y
WhatsApp local, establecer `JARVIS_DEMO_CATALOG=1` en `.env`; el script conserva
la configuración existente. El perfil GPU predeterminado no activa datos demo.

También se puede transportar un `git bundle` de la rama y clonarlo sin servidor
Git; los modelos seguirán descargándose en el primer arranque.

Si se copia `paseo-aranjuez-torre.bundle` a la torre:

```bash
git clone --branch feat/jarvis-grounded-kiosk /ruta/paseo-aranjuez-torre.bundle paseo-aranjuez-digital
cd paseo-aranjuez-digital
bash scripts/start-tower.sh
```

El bundle es una instantánea Git sin modelos, secretos locales ni conversaciones
de SQLite. Para actualizaciones posteriores, reemplazar su remoto `origin` por
la URL del repositorio compartido usando `git remote set-url origin URL`.

## Qué se levanta

| Servicio | Función | Persistencia |
| --- | --- | --- |
| `jarvis` | API, UI con avatar, RAG estricto y proxy de audio | SQLite en `jarvis-data` |
| `voice` | Whisper multilingüe `small`, Kokoro `ef_dora`, CUDA | Modelos en `voice-models` |

La semilla incluye las 20 fichas curadas y una instantánea de las 58 adicionales
del directorio oficial. La instantánea conserva sus fechas y fuentes originales. Arrancar no
vuelve a consultar el directorio ni sobrescribe fichas existentes. Las búsquedas
normales no necesitan nube. El clima necesita Internet y el QR actual puede
depender de un servicio externo: funcionamiento local de voz no significa que
todas las integraciones ya sean offline.

Sólo la API se publica y queda enlazada a `127.0.0.1`. El servicio GPU es privado
dentro de Docker. Para otros kioscos hacen falta HTTPS y la configuración de red
de Windows; abrir `http://IP:8000` por LAN no basta para obtener permiso de
micrófono. Ese despliegue presencial se describe en el plan futuro y no se activa
automáticamente con este script.

## Uso cotidiano

```bash
docker compose ps
docker compose logs --tail 100 voice jarvis
docker compose stop
docker compose start
```

Para actualizar el código y reconstruir:

```bash
git pull --ff-only
bash scripts/start-tower.sh
```

No usar `docker compose down -v` para una parada normal: elimina catálogo y
modelos descargados. Los reinicios normales preservan ambos volúmenes. Docker
Desktop debe arrancar con la sesión de Windows y la torre no debe entrar en
suspensión durante una demo. Una instalación 24/7 requiere supervisión y probar
el reinicio de Windows; `restart: unless-stopped` por sí solo no lo garantiza.

## Medir antes de prometer latencia

```bash
docker compose exec -T jarvis python -m jarvis.benchmark --runs 5
```

Para incluir transcripción, grabar una consulta real como WAV mono PCM16 a
16 kHz, de hasta 15 segundos:

```bash
docker compose cp consulta.wav jarvis:/tmp/consulta.wav
docker compose exec -T jarvis python -m jarvis.benchmark --runs 20 --wav /tmp/consulta.wav
```

La herramienta informa transcripción, chat, tiempo hasta primer PCM, mediana,
p95 y RTF. **RTF menor que 1** significa que genera audio más rápido de lo que se
reproduce. La medición no incluye el tiempo de silencio del micrófono ni la
salida física del altavoz. La consola del navegador informa adicionalmente el
tiempo hasta programar el primer sonido del TTS.

Meta inicial: alrededor de 1–1,5 segundos desde el final de una consulta corta
hasta empezar a oír la respuesta en LAN. Es una meta pendiente de comprobar en
la 4070, no un resultado obtenido en la Mac. Medir primero un usuario y después
carga concurrente; este perfil admite una inferencia de voz a la vez y rechaza
ocupación con 503, en lugar de acumular una cola sin límite.

## Por qué esta configuración y qué falta

- Los modelos se cargan una vez y se calientan antes de aceptar tráfico. Se evita
  arrancar Whisper y cargar pesos en cada consulta.
- Kokoro recibe segmentos cortos en español; el servidor entrega PCM por
  segmentos y el navegador lo reproduce antes de tener la respuesta completa.
  Esto es streaming por segmentos, no generación neuronal muestra por muestra.
- La boca del avatar usa el volumen del audio real. El botón de micrófono y una
  nueva consulta cancelan reproducción y descarga pendientes.
- La espera tras silencio baja a 650 ms en el perfil GPU. El detector actual usa
  energía del micrófono; hay que probarlo con música, conversaciones y pausas.
- El RAG estricto responde desde evidencia sin ejecutar un LLM adicional.

No hay evidencia para llamarlo “la mejor implementación posible”. Es una base
simple y medible para esta GPU. Aún falta comparar calidad y latencia de `small`
frente a `large-v3-turbo`, sustituir detección por energía por VAD robusto,
transcribir mientras el usuario habla y resolver interrupciones automáticas con
cancelación de eco. Añadir un LLM local requeriría además medir su consumo de
VRAM compartida con voz. El RAG no elimina por sí mismo las alucinaciones de un
LLM; se mantiene la salida estricta en este despliegue.

Cambiar `WHISPER_MODEL` o `KOKORO_VOICE` en `.env` y ejecutar de nuevo el script
permite comparar. `ef_dora`, `em_alex` y `em_santa` son las voces admitidas. Tras
descargar y probar la configuración elegida, `HF_HUB_OFFLINE=1` permite comprobar
que los modelos arrancan desde caché sin consultar Hugging Face.

Pocket TTS queda como experimento posterior: su cifra publicada de primer audio
no es una medición en esta torre, y su implementación está orientada a CPU; no
se debe asumir que la 4070 lo acelera automáticamente.

## Verificación disponible y pendiente

Los tests del repositorio verifican contratos HTTP, transmisión parcial,
cancelación, tramas incompletas, validación de WAV y carga del catálogo. Se puede
validar la composición con `JARVIS_INGEST_TOKEN=test docker compose config --quiet`.

El build CUDA y la calidad/latencia reales requieren ejecutar el script en la
torre. En la Mac de preparación el daemon Docker no está iniciado y no existe
una GPU NVIDIA: los tests con dobles de modelos no validan CUDA. Las dependencias
principales e imágenes usan versiones concretas; para un despliegue de producción
se deben fijar también dependencias transitivas, revisiones de modelos y digests
de imágenes después de certificar una combinación en la torre.

Referencias: [Kokoro oficial](https://github.com/hexgrad/kokoro),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper),
[GPU en Docker Compose](https://docs.docker.com/compose/how-tos/gpu-support/).
