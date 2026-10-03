# Acceso a fichas desde teléfono

## Implementado

El kiosco obtiene el QR de `/qr/destination/{id}`. Se genera en Jarvis con `qrcode==8.2`, sin enviar el enlace a un generador externo. La imagen usa SVG, fondo blanco y margen de cuatro módulos. [Referencia de la biblioteca](https://pypi.org/project/qrcode/8.2/).

Mientras `JARVIS_MOBILE_BASE_URL` esté vacía, el QR abre la fuente pública del negocio. La ficha local funciona en `/destination/{id}`, pero localhost en un teléfono apunta al propio teléfono.

`compose.mobile.yaml` agrega una pasarela Nginx en 8080 que solo permite consultar `/destination/`. Chat, voz, administración e historial no se publican en esa pasarela. [Referencia de restricción de métodos](https://nginx.org/en/docs/http/ngx_http_core_module.html#limit_except).

## Fichas en el mismo Wi-Fi

1. Confirmar la IPv4 de la PC en la red usada por el teléfono; evitar interfaces de WSL, VPN y adaptadores virtuales. PC y teléfono deben compartir una red que permita comunicación entre clientes.
2. En `.env`, configurar `JARVIS_MOBILE_BIND` con esa IPv4, `JARVIS_MOBILE_PORT=8080` y `JARVIS_MOBILE_BASE_URL=http://<IPv4-PC>:8080`. Mantener el puerto 8000 en localhost.
3. Desde Ubuntu, en el repositorio, aplicar:

   ```bash
   docker compose -f compose.yaml -f compose.mobile.yaml up -d jarvis mobile
   ```

4. Si Windows bloquea el acceso, permitir solamente TCP 8080 para la aplicación/pasarela en la red privada local. No abrir el router ni cambiar el perfil de una red pública para esta demo.
5. Abrir una ficha desde el teléfono y escanear un QR del kiosco. Verificar que nombre, piso, local y fuente corresponden al destino elegido. Repetir si cambia la IP de la PC.

No se ha activado acceso LAN: falta confirmar la modalidad del teléfono y la red. La configuración predeterminada del archivo adicional también escucha solo en `127.0.0.1`.

## Conversar con micrófono o abrir desde fuera del Wi-Fi

Hace falta un origen HTTPS confiable para el navegador y un despliegue del kiosco/API con límites de uso. La pasarela de fichas no habilita chat ni voz. Confirmar dominio o proveedor de acceso, certificado y alcance antes de configurar esa modalidad. Una IP HTTP en la LAN sirve para fichas, pero no satisface el requisito de contexto seguro del micrófono.

## Recomendación para el reto

Usar voz en el kiosco de esta PC y QR de fichas en el mismo Wi-Fi. Reservar el chat móvil con HTTPS para la etapa siguiente si no es parte indispensable de la demostración. Probar con el teléfono real en el lugar; cambiar una variable no acredita conectividad.

## Interfaz adaptable (3 de octubre de 2026)

El kiosco web ahora adapta paneles a móvil/tableta, con pestañas y tarjetas desplazables completas, controles táctiles y ajuste al teclado. Esto cubre la interfaz web móvil; el acceso desde otro dispositivo sigue requiriendo la configuración de red/HTTPS indicada arriba. No hay aplicación nativa, modo offline ni publicación en tiendas.
