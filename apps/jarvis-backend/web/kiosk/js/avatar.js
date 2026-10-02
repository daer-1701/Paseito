// Avatar cochabambino animado en SVG: sombrero blanco de copa alta, trenzas con tullmas,
// manta con franja de aguayo y aretes dorados. La boca sigue el volumen real del audio.
//
//   const avatar = new Avatar(document.getElementById("avatar"));
//   avatar.desbloquear();                 // dentro de un clic (política de audio del navegador)
//   await avatar.hablarAudio(urlMp3);     // reproduce y mueve la boca
//   avatar.hablarSimulado(true / false);  // para voces sin audio analizable (speechSynthesis)
//   avatar.estado = "escuchando" | "pensando" | "normal";

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
    this.estado = "normal";
    this.apertura = 0;
    this.ancho = 1;
    this.analizador = null;
    this.simulado = false;
    this.proximoParpadeo = performance.now() + 2000;
    this.parpadeo = 0;
    this._cuadro = this._cuadro.bind(this);
    requestAnimationFrame(this._cuadro);
  }

  desbloquear() {
    contextoAudio ??= new (window.AudioContext || window.webkitAudioContext)();
    if (contextoAudio.state === "suspended") contextoAudio.resume();
  }

  // El avatar 2D no tiene brazos ni cámara: se aceptan para ser intercambiable con Avatar3D.
  gesto() {}
  encuadre() {}

  /** Reproduce un audio (URL) moviendo la boca con su volumen. Resuelve al terminar o al llamar a callar(). */
  hablarAudio(url, { alProgresar } = {}) {
    this.desbloquear();
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
      const terminar = () => {
        if (this.audio === audio) { this.analizador = null; this.audio = null; }
        alProgresar?.(1);
        resolve();
      };
      audio.ontimeupdate = () => audio.duration && alProgresar?.(audio.currentTime / audio.duration);
      audio.onended = terminar;
      audio.onpause = terminar;
      audio.onerror = reject;
      audio.play().catch(reject);
    });
  }

  hablarSimulado(activo) {
    this.simulado = activo;
  }

  callar() {
    if (this.audio) this.audio.pause();
    this.simulado = false;
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
    let objetivo = 0;
    if (this.analizador) {
      objetivo = Math.min(1, Math.max(0, (this._volumen() - 0.015) * 7));
    } else if (this.simulado) {
      objetivo = 0.2 + 0.6 * Math.abs(Math.sin(t * 12.7) * Math.sin(t * 5.3));
    }
    // abre rápido y cierra un poco más lento, como una boca real
    this.apertura += (objetivo - this.apertura) * (objetivo > this.apertura ? 0.5 : 0.25);
    this.ancho += ((objetivo > 0.5 ? 0.88 : 1) + Math.sin(t * 9) * 0.04 * objetivo - this.ancho) * 0.2;
    const hablando = this.apertura > 0.05;

    this._dibujarBoca();
    this._parpadear(ahora);

    // respiración, cabeceo al hablar y vaivén de los aretes
    const giro = hablando ? Math.sin(t * 2.4) * 1.8 + Math.sin(t * 5.1) * 0.6 : Math.sin(t * 0.6) * 0.8;
    const asiente = hablando ? Math.sin(t * 3.3) * 1.5 : 0;
    this.el.respira.setAttribute("transform", `translate(0 ${Math.sin(t * 1.6) * 1.5})`);
    this.el.cabeza.setAttribute("transform", `rotate(${giro} 200 330) translate(0 ${asiente})`);
    const vaiven = -giro * 3 + Math.sin(t * 2) * 2;
    this.el.areteIzq.setAttribute("transform", `rotate(${vaiven} 138 274)`);
    this.el.areteDer.setAttribute("transform", `rotate(${vaiven} 262 274)`);

    // cejas y mirada según el estado
    const cejas = this.estado === "escuchando" ? -5 : this.estado === "pensando" ? -2 : hablando ? -this.apertura * 3 : 0;
    this.el.cejaIzq.setAttribute("transform", `translate(0 ${cejas})`);
    this.el.cejaDer.setAttribute("transform", `translate(0 ${this.estado === "pensando" ? -6 : cejas})`);
    const mirada = this.estado === "pensando" ? "translate(-3 -3)" : `translate(${Math.sin(t * 0.37) * 1.5} 0)`;
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
    const w = 19 * this.ancho;
    const h = 1 + 15 * this.apertura;
    const sonrisa = 3 * (1 - this.apertura);
    const yc = y - sonrisa;
    this.el.interior.setAttribute("d",
      `M${x - w} ${yc} Q${x} ${y - 2 - h * 0.25} ${x + w} ${yc} Q${x} ${y + h * 1.3} ${x - w} ${yc} Z`);
    this.el.dientes.setAttribute("d",
      `M${x - w * 0.6} ${y - 1} Q${x} ${y - 2 - h * 0.25} ${x + w * 0.6} ${y - 1} Q${x} ${y + h * 0.3} ${x - w * 0.6} ${y - 1} Z`);
    this.el.dientes.setAttribute("opacity", Math.min(1, Math.max(0, (h - 4) / 6)));
    this.el.labioSup.setAttribute("d",
      `M${x - w} ${yc} Q${x - w * 0.5} ${y - 5 - h * 0.25} ${x} ${y - 3 - h * 0.25} Q${x + w * 0.5} ${y - 5 - h * 0.25} ${x + w} ${yc}`);
    this.el.labioInf.setAttribute("d",
      `M${x - w} ${yc} Q${x} ${y + h * 1.3 + 4} ${x + w} ${yc}`);
  }
}
