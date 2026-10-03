// Avatar cochabambino animado en SVG: sombrero blanco de copa alta, trenzas con tullmas,
// manta con franja de aguayo y aretes dorados. La boca sigue el volumen real del audio.
//
//   const avatar = new Avatar(document.getElementById("avatar"));
//   avatar.desbloquear();                 // dentro de un clic (política de audio del navegador)
//   await avatar.hablarAudio(urlMp3, { alProgresar, texto });  // con texto, la boca forma cada sonido
//   avatar.hablarSimulado(true / false);  // para voces sin audio analizable (speechSynthesis); decirPalabra(p)
//   avatar.estado = "escuchando" | "pensando" | "normal";
//   avatar.asentir();  avatar.sonreir(intensidad, ms);  avatar.mirarA(x, y, ms);

import { FORMAS, formaEn, formaPorVolumen, palabraEn, planDePalabra, prepararPlan } from "./habla.js";

const CLAVES_BOCA = Object.keys(FORMAS.reposo);
const SVG_NS = "http://www.w3.org/2000/svg";
const PIEL = "#c98b5e";
const PIEL_SOMBRA = "#b07548";
const CABELLO = "#1c1311";
const BOCA = { x: 200, y: 304 };

const PLANTILLA = `
<svg viewBox="0 0 400 520" xmlns="${SVG_NS}" role="img" aria-label="Avatar del asistente del Paseo Aranjuez">
  <defs>
    <clipPath id="av-cuerpo"><path d="M64 520 Q72 404 150 374 Q200 392 250 374 Q328 404 336 520 Z"/></clipPath>
    <linearGradient id="av-manta" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#8c2346"/><stop offset="1" stop-color="#5e1430"/>
    </linearGradient>
    <linearGradient id="av-sombrero" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#e9e4d8"/><stop offset=".45" stop-color="#ffffff"/><stop offset="1" stop-color="#ddd6c6"/>
    </linearGradient>
    <radialGradient id="av-cara" cx=".45" cy=".4" r=".7">
      <stop offset="0" stop-color="#d69a6c"/><stop offset="1" stop-color="${PIEL}"/>
    </radialGradient>
  </defs>

  <g id="av-respira">
    <!-- cuerpo: manta, blusa, franja de aguayo y tupu -->
    <path d="M64 520 Q72 404 150 374 Q200 392 250 374 Q328 404 336 520 Z" fill="url(#av-manta)"/>
    <g clip-path="url(#av-cuerpo)">
      ${aguayo(446)}
      <path d="M64 520 L336 520" stroke="#3d0c20" stroke-width="10"/>
    </g>
    <path d="M168 371 Q200 426 232 371 Q200 384 168 371 Z" fill="#f7f1e8"/>
    <path d="M176 380 Q200 414 224 380" fill="none" stroke="#d6336c" stroke-width="2" stroke-dasharray="3 4"/>
    <circle cx="200" cy="430" r="7" fill="#e7b73a" stroke="#a37a12" stroke-width="2"/>
    <path d="M200 437 L200 452" stroke="#a37a12" stroke-width="2"/>

    <!-- trenzas sobre la manta, con tullmas de lana -->
    ${trenza(152, 262, 128, 456)}
    ${trenza(248, 262, 272, 456)}
    ${tullma(128, 462)}
    ${tullma(272, 462)}

    <!-- cuello -->
    <path d="M178 318 L176 376 Q200 388 224 376 L222 318 Z" fill="${PIEL_SOMBRA}"/>

    <g id="av-cabeza">
      <!-- cabello de atrás -->
      <ellipse cx="200" cy="246" rx="71" ry="80" fill="${CABELLO}"/>

      <!-- orejas y aretes -->
      <ellipse cx="139" cy="262" rx="9" ry="14" fill="${PIEL_SOMBRA}"/>
      <ellipse cx="261" cy="262" rx="9" ry="14" fill="${PIEL_SOMBRA}"/>
      <g id="av-arete-izq">${arete(138, 274)}</g>
      <g id="av-arete-der">${arete(262, 274)}</g>

      <!-- cara -->
      <ellipse cx="200" cy="256" rx="62" ry="74" fill="url(#av-cara)"/>
      <ellipse cx="164" cy="287" rx="13" ry="7" fill="#e06a64" opacity=".35"/>
      <ellipse cx="236" cy="287" rx="13" ry="7" fill="#e06a64" opacity=".35"/>

      <!-- cabello de adelante con raya al medio -->
      <path d="M138 252 Q132 186 200 180 Q268 186 262 252 Q254 216 200 211 Q146 216 138 252 Z" fill="${CABELLO}"/>
      <path d="M200 194 L200 210" stroke="#3a2a25" stroke-width="2"/>

      <!-- cejas -->
      <path id="av-ceja-izq" d="M163 229 Q177 220 191 227" fill="none" stroke="#2a1a14" stroke-width="4" stroke-linecap="round"/>
      <path id="av-ceja-der" d="M209 227 Q223 220 237 229" fill="none" stroke="#2a1a14" stroke-width="4" stroke-linecap="round"/>

      <!-- ojos -->
      <g id="av-ojo-izq">${ojo(177, 249)}</g>
      <g id="av-ojo-der">${ojo(223, 249)}</g>

      <!-- nariz -->
      <path d="M201 256 Q197 272 192 279 Q200 285 208 279" fill="none" stroke="#9c6440" stroke-width="2.5" stroke-linecap="round"/>

      <!-- boca (se regenera en cada cuadro) -->
      <g id="av-boca">
        <path id="av-boca-interior" fill="#5a1a1f"/>
        <path id="av-dientes" fill="#fbf7f0"/>
        <path id="av-labio-sup" fill="none" stroke="#a8434a" stroke-width="4" stroke-linecap="round"/>
        <path id="av-labio-inf" fill="none" stroke="#b84d55" stroke-width="5" stroke-linecap="round"/>
      </g>

      <!-- sombrero blanco cochabambino de copa alta con cinta negra -->
      <g transform="rotate(-4 200 190)">
        <path d="M141 192 L149 104 Q200 90 251 104 L259 192 Z" fill="url(#av-sombrero)" stroke="#cfc7b4" stroke-width="1.5"/>
        <ellipse cx="200" cy="103" rx="51" ry="10" fill="#ffffff" stroke="#d8d1c0" stroke-width="1.5"/>
        <path d="M143 170 L257 170 L259 190 L141 190 Z" fill="#161616"/>
        <path d="M150 172 L250 172" stroke="#3a3a3a" stroke-width="1.5"/>
        <ellipse cx="200" cy="192" rx="94" ry="17" fill="url(#av-sombrero)" stroke="#cfc7b4" stroke-width="1.5"/>
      </g>
    </g>
  </g>
</svg>`;

function trenza(x1, y1, x2, y2) {
  const cx = (x1 + x2) / 2 + (x2 > x1 ? 8 : -8);
  const d = `M${x1} ${y1} Q${cx} ${(y1 + y2) / 2} ${x2} ${y2}`;
  return `<path d="${d}" fill="none" stroke="${CABELLO}" stroke-width="22" stroke-linecap="round"/>
          <path d="${d}" fill="none" stroke="#3a2a25" stroke-width="16" stroke-dasharray="6 9"/>`;
}

function tullma(x, y) {
  return `<path d="M${x} ${y - 10} L${x} ${y}" stroke="#d62f5b" stroke-width="4"/>
          <circle cx="${x}" cy="${y + 6}" r="9" fill="#d62f5b"/>
          <circle cx="${x - 5}" cy="${y + 14}" r="6" fill="#f2b705"/>
          <circle cx="${x + 5}" cy="${y + 14}" r="6" fill="#1f9d55"/>`;
}

function aguayo(y) {
  const franjas = [["#f2b705", 5], ["#d62f5b", 7], ["#1f9d55", 4], ["#2b59c3", 6], ["#d62f5b", 7], ["#f2b705", 5]];
  let salida = "";
  let actual = y;
  for (const [color, alto] of franjas) {
    salida += `<rect x="0" y="${actual}" width="400" height="${alto}" fill="${color}"/>`;
    actual += alto;
  }
  // rombos típicos del tejido sobre la franja central
  for (let x = 40; x < 380; x += 26) {
    salida += `<path d="M${x} ${y + 17} l7 -6 l7 6 l-7 6 Z" fill="#fff4d6" opacity=".9"/>`;
  }
  return salida;
}

function arete(x, y) {
  return `<circle cx="${x}" cy="${y}" r="3" fill="#e7b73a"/>
          <path d="M${x} ${y + 2} L${x} ${y + 10}" stroke="#c99a1e" stroke-width="1.5"/>
          <path d="M${x - 7} ${y + 12} Q${x} ${y + 34} ${x + 7} ${y + 12} Z" fill="#e7b73a" stroke="#a37a12" stroke-width="1"/>
          <circle cx="${x}" cy="${y + 18}" r="2.5" fill="#d62f5b"/>`;
}

function ojo(x, y) {
  return `<ellipse cx="${x}" cy="${y}" rx="11.5" ry="7.5" fill="#fffaf3"/>
          <g class="av-iris"><circle cx="${x}" cy="${y}" r="6" fill="#3b2416"/>
          <circle cx="${x}" cy="${y}" r="3" fill="#120a06"/>
          <circle cx="${x + 2}" cy="${y - 2}" r="1.6" fill="#fff"/></g>
          <path d="M${x - 12} ${y - 2} Q${x} ${y - 11} ${x + 12} ${y - 2}" fill="none" stroke="#1c1311" stroke-width="2.5" stroke-linecap="round"/>`;
}

let contextoAudio = null;

export class Avatar {
  constructor(contenedor) {
    contenedor.innerHTML = PLANTILLA;
    const $ = (id) => contenedor.querySelector("#" + id);
    this.el = {
      respira: $("av-respira"), cabeza: $("av-cabeza"),
      ojoIzq: $("av-ojo-izq"), ojoDer: $("av-ojo-der"),
      cejaIzq: $("av-ceja-izq"), cejaDer: $("av-ceja-der"),
      areteIzq: $("av-arete-izq"), areteDer: $("av-arete-der"),
      interior: $("av-boca-interior"), dientes: $("av-dientes"),
      labioSup: $("av-labio-sup"), labioInf: $("av-labio-inf"),
      iris: contenedor.querySelectorAll(".av-iris"),
    };
    this.contenedor = contenedor;
    this.estado = "normal";
    this.boca = { ...FORMAS.reposo };
    this._forma = { ...FORMAS.reposo };
    this.sonrisa = 0.3;
    this.intensidadSonrisa = 0;
    this.finSonrisa = 0;
    this.plan = null;
    this.palabraSim = null;
    this.asentirDesde = -1e9;
    this.mirarHasta = 0;
    this.mirarHacia = { x: 0, y: 0 };
    this.analizador = null;
    this.simulado = false;
    this.proximoParpadeo = performance.now() + 2000;
    this.parpadeo = 0;
    this._ultimo = performance.now();
    this._cuadro = this._cuadro.bind(this);
    requestAnimationFrame(this._cuadro);
  }

  asentir() {
    const ahora = performance.now();
    if (ahora - this.asentirDesde > 900) this.asentirDesde = ahora;
  }

  sonreir(intensidad = 1, duracion = 2500) {
    this.intensidadSonrisa = intensidad;
    this.finSonrisa = performance.now() + duracion;
  }

  /** Mira un punto de la pantalla (px): solo los ojos, el 2D no tiene brazos. */
  mirarA(x, y, duracion = 1500) {
    const r = this.contenedor.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height * 0.45;
    const d = Math.hypot(x - cx, y - cy) || 1;
    this.mirarHacia = { x: (x - cx) / d, y: (y - cy) / d };
    this.mirarHasta = performance.now() + duracion;
  }

  señalar(x, y, duracion = 2600) { this.mirarA(x, y, Math.min(duracion, 1600)); }

  decirPalabra(palabra) {
    if (palabra) this.palabraSim = { plan: planDePalabra(palabra), desde: performance.now() };
  }

  desbloquear() {
    contextoAudio ??= new (window.AudioContext || window.webkitAudioContext)();
    if (contextoAudio.state === "suspended") contextoAudio.resume();
  }

  // El avatar 2D no tiene brazos ni cámara: se aceptan para ser intercambiable con Avatar3D.
  gesto() {}
  encuadre() {}

  /**
   * Reproduce un audio (URL) moviendo la boca. Con `texto` la boca toma la forma de cada sonido y
   * `alProgresar` avanza palabra por palabra; sin texto sigue el volumen. Resuelve al terminar o al callar().
   */
  hablarAudio(url, { alProgresar, texto } = {}) {
    this.desbloquear();
    const plan = texto ? prepararPlan(url, texto, contextoAudio).catch(() => null) : Promise.resolve(null);
    return new Promise((resolve, reject) => {
      const audio = new Audio(url);
      const fuente = contextoAudio.createMediaElementSource(audio);
      const analizador = contextoAudio.createAnalyser();
      analizador.fftSize = 512;
      fuente.connect(analizador);
      analizador.connect(contextoAudio.destination);
      this.audio = audio;
      this.analizador = analizador;
      this.buffer = new Uint8Array(analizador.fftSize);
      this.plan = null;
      let hecho = false;
      let ultimaPalabra = -2;
      const terminar = () => {
        if (hecho) return;
        hecho = true;
        if (this.audio === audio) { this.analizador = null; this.audio = null; this.plan = null; }
        if (this._terminar === terminar) this._terminar = null;
        alProgresar?.(1);
        resolve();
      };
      this._terminar = terminar;
      audio.ontimeupdate = () => {
        if (!audio.duration || this.plan) return;
        alProgresar?.(audio.currentTime / audio.duration);
      };
      this._alPalabra = (k, n) => {
        if (k >= 0 && k !== ultimaPalabra) { ultimaPalabra = k; alProgresar?.(Math.min(0.99, (k + 0.5) / n)); }
      };
      audio.onended = terminar;
      audio.onpause = terminar;
      audio.onerror = reject;
      Promise.race([plan, new Promise((ok) => setTimeout(ok, 300))]).then((listo) => {
        if (this.audio !== audio) return;
        if (listo) this.plan = listo;
        else plan.then((tarde) => { if (tarde && this.audio === audio) this.plan = tarde; });
        audio.play().catch(reject);
      });
    });
  }

  hablarSimulado(activo) {
    this.simulado = activo;
    if (!activo) this.palabraSim = null;
  }

  callar() {
    if (this.audio) this.audio.pause();
    this._terminar?.();
    this.simulado = false;
    this.palabraSim = null;
    this.plan = null;
  }

  _volumen() {
    if (!this.analizador) return 0;
    this.analizador.getByteTimeDomainData(this.buffer);
    let suma = 0;
    for (const v of this.buffer) suma += ((v - 128) / 128) ** 2;
    return Math.sqrt(suma / this.buffer.length);
  }

  _cuadro(ahora) {
    const t = ahora / 1000;
    const dt = Math.min(0.12, (ahora - this._ultimo) / 1000);
    this._ultimo = ahora;
    const suave = (k) => 1 - Math.exp(-dt * k);

    // boca: forma del sonido (plan alineado al audio), de la palabra (voz del navegador) o del volumen
    const objetivo = this._forma;
    if (this.analizador) {
      const tAudio = this.audio?.currentTime ?? 0;
      if (this.plan) {
        formaEn(this.plan, tAudio, objetivo);
        this._alPalabra?.(palabraEn(this.plan, tAudio), this.plan.palabras.length);
      } else {
        formaPorVolumen(this._volumen(), t, objetivo);
      }
    } else if (this.simulado && this.palabraSim) {
      formaEn(this.palabraSim.plan, (ahora - this.palabraSim.desde) / 1000, objetivo);
    } else if (this.simulado) {
      formaPorVolumen(0.015 + (0.2 + 0.6 * Math.abs(Math.sin(t * 12.7) * Math.sin(t * 5.3))) / 7, t, objetivo);
    } else {
      Object.assign(objetivo, FORMAS.reposo);
    }
    for (const k of CLAVES_BOCA) this.boca[k] += (objetivo[k] - this.boca[k]) * suave(objetivo[k] > this.boca[k] ? 30 : 20);
    const sonrisaObjetivo = ahora < this.finSonrisa ? this.intensidadSonrisa
      : this.estado === "pensando" ? 0.1 : this.estado === "escuchando" ? 0.4 : 0.3;
    this.sonrisa += (sonrisaObjetivo - this.sonrisa) * suave(4);
    const hablando = this.boca.abre > 0.05;

    this._dibujarBoca();
    this._parpadear(ahora);

    // respiración, cabeceo al hablar (y al asentir) y vaivén de los aretes
    const d = (ahora - this.asentirDesde) / 1000;
    const nod = d < 0.8 ? 7 * Math.sin((Math.PI * d) / 0.4) ** 2 * (1 - d) : 0;
    const giro = hablando ? Math.sin(t * 2.4) * 1.8 + Math.sin(t * 5.1) * 0.6 : Math.sin(t * 0.6) * 0.8;
    const asiente = (hablando ? Math.sin(t * 3.3) * 1.5 : 0) + nod;
    this.el.respira.setAttribute("transform", `translate(0 ${Math.sin(t * 1.6) * 1.5})`);
    this.el.cabeza.setAttribute("transform", `rotate(${giro} 200 330) translate(0 ${asiente})`);
    const vaiven = -giro * 3 + Math.sin(t * 2) * 2;
    this.el.areteIzq.setAttribute("transform", `rotate(${vaiven} 138 274)`);
    this.el.areteDer.setAttribute("transform", `rotate(${vaiven} 262 274)`);

    // cejas y mirada según el estado
    const cejas = this.estado === "escuchando" ? -5 : this.estado === "pensando" ? -2 : hablando ? -this.boca.abre * 3 : 0;
    this.el.cejaIzq.setAttribute("transform", `translate(0 ${cejas})`);
    this.el.cejaDer.setAttribute("transform", `translate(0 ${this.estado === "pensando" ? -6 : cejas})`);
    const mirada = this.estado === "pensando" ? "translate(-3 -3)"
      : ahora < this.mirarHasta ? `translate(${this.mirarHacia.x * 3.5} ${this.mirarHacia.y * 2.5})`
      : `translate(${Math.sin(t * 0.37) * 1.5} 0)`;
    for (const iris of this.el.iris) iris.setAttribute("transform", mirada);

    requestAnimationFrame(this._cuadro);
  }

  _parpadear(ahora) {
    if (ahora > this.proximoParpadeo) {
      this.parpadeo = ahora;
      this.proximoParpadeo = ahora + 2200 + Math.random() * 3500;
    }
    const fase = (ahora - this.parpadeo) / 140;
    const cierre = fase >= 0 && fase < 2 ? 1 - Math.abs(1 - fase) : 0;
    const escala = Math.max(0.08, 1 - cierre);
    this.el.ojoIzq.setAttribute("transform", `translate(177 249) scale(1 ${escala}) translate(-177 -249)`);
    this.el.ojoDer.setAttribute("transform", `translate(223 249) scale(1 ${escala}) translate(-223 -249)`);
  }

  _dibujarBoca() {
    const { x, y } = BOCA;
    const b = this.boca;
    // "o"/"u" juntan las comisuras, "e"/"i" las estiran; "m/b/p" aprietan los labios cerrados
    const w = 19 * b.ancho * (1 - 0.3 * b.redondo) * (1 + 0.08 * this.sonrisa);
    const h = 1 + 15 * b.abre * (1 + 0.15 * b.redondo) - b.presion * 0.8;
    const sonrisa = 10 * this.sonrisa * (1 - b.abre) * (1 - b.redondo);
    const yc = y - sonrisa;
    this.el.interior.setAttribute("d",
      `M${x - w} ${yc} Q${x} ${y - 2 - h * 0.25} ${x + w} ${yc} Q${x} ${y + h * 1.3} ${x - w} ${yc} Z`);
    this.el.dientes.setAttribute("d",
      `M${x - w * 0.6} ${y - 1} Q${x} ${y - 2 - h * 0.25} ${x + w * 0.6} ${y - 1} Q${x} ${y + h * 0.3} ${x - w * 0.6} ${y - 1} Z`);
    this.el.dientes.setAttribute("opacity", Math.min(1, Math.max(0, (h - 3) / 5)) * (0.3 + 0.7 * b.dientes));
    this.el.labioSup.setAttribute("d",
      `M${x - w} ${yc} Q${x - w * 0.5} ${y - 5 - h * 0.25} ${x} ${y - 3 - h * 0.25} Q${x + w * 0.5} ${y - 5 - h * 0.25} ${x + w} ${yc}`);
    this.el.labioInf.setAttribute("d",
      `M${x - w} ${yc} Q${x} ${y + h * 1.3 + 4} ${x + w} ${yc}`);
  }
}
