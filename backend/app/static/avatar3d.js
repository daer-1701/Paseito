// Paseito en 3D (Three.js): cochabambina con sombrero blanco de copa alta, trenzas con tullmas,
// manta de aguayo y pollera, sobre una plataforma frente al Tunari y el Cristo de la Concordia.
// Misma API que el avatar 2D (avatar.js) para poder intercambiarlos:
//
//   const avatar = new Avatar3D(contenedor);     // lanza un error si no hay WebGL
//   avatar.desbloquear();                        // dentro de un clic (política de audio)
//   await avatar.hablarAudio(url, { alProgresar: f => ... });
//   avatar.hablarSimulado(true / false);
//   avatar.estado = "normal" | "escuchando" | "pensando";
//   avatar.gesto("saludar" | "presentar" | "pensar" | "normal");
//   avatar.encuadre({ arriba, abajo, izquierda, derecha });  // px que tapa la interfaz

import * as THREE from "three";

const C = {
  piel: 0xc68a5c, pielOscura: 0xa96f46, cabello: 0x1e1412, sombrero: 0xf7f3ea, cinta: 0x151515,
  blusa: 0xfbf7ef, pollera: 0xc2185b, oro: 0xe7b73a, labio: 0xb4505a, boca: 0x3a0d12,
};
const COLOR_ESTADO = { normal: 0xe7b73a, escuchando: 0xff5470, pensando: 0x8f7bff };

// pose de cada brazo: [hombro x, y, z, codo x, y, z]; s = +1 brazo izquierdo de Paseito (derecha de la pantalla)
const POSES = {
  normal: (s) => [-0.2, 0, s * 0.18, -1.3, 0, -s * 0.55],
  saludar: (s) => (s > 0 ? [-0.25, 0, 2.55, -0.25, 0, 0.35] : POSES.normal(s)),
  presentar: (s) => (s > 0 ? [-0.95, 0, 0.6, -0.45, 0, 0.15] : POSES.normal(s)),
  pensar: (s) => (s < 0 ? [-0.85, 0, -0.1, -2.0, 0, 0.65] : POSES.normal(s)),
};

function aleatorio(semilla) {
  let s = semilla;
  return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
}

function colocar(objeto, x, y, z) {
  objeto.position.set(x, y, z);
  return objeto;
}

function lienzo(ancho, alto, dibujar) {
  const c = document.createElement("canvas");
  c.width = ancho;
  c.height = alto;
  dibujar(c.getContext("2d"), ancho, alto);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

const texturaRadial = () => lienzo(128, 128, (g, w) => {
  const r = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2);
  r.addColorStop(0, "rgba(255,255,255,1)");
  r.addColorStop(0.35, "rgba(255,255,255,.45)");
  r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r;
  g.fillRect(0, 0, w, w);
});

// Sin flipY, la fila superior del lienzo queda en el borde inferior de la manta.
const texturaAguayo = () => lienzo(1024, 256, (g, w, h) => {
  g.fillStyle = "#b03a63";
  g.fillRect(0, 0, w, h);
  g.globalAlpha = 0.1;
  for (let x = 0; x < w; x += 8) { g.fillStyle = "#000"; g.fillRect(x, 0, 2, h); }
  g.globalAlpha = 1;
  const franjas = [["#3d0c20", 10], ["#f2b705", 9], ["#d62f5b", 13], ["#1f9d55", 7], ["#2b59c3", 22], ["#1f9d55", 7], ["#d62f5b", 13], ["#f2b705", 9]];
  let y = 0;
  let centroAzul = 0;
  for (const [color, alto] of franjas) {
    g.fillStyle = color;
    g.fillRect(0, y, w, alto);
    if (color === "#2b59c3") centroAzul = y + alto / 2;
    y += alto;
  }
  g.fillStyle = "#fff4d6";
  for (let x = 12; x < w; x += 32) {
    g.beginPath();
    g.moveTo(x, centroAzul - 8); g.lineTo(x + 8, centroAzul); g.lineTo(x, centroAzul + 8); g.lineTo(x - 8, centroAzul);
    g.fill();
  }
});

const texturaPlataforma = () => lienzo(512, 512, (g, w) => {
  const c = w / 2;
  g.fillStyle = "#2a0f1b";
  g.fillRect(0, 0, w, w);
  g.strokeStyle = "#e7b73a";
  g.lineWidth = 3;
  for (const r of [238, 200, 120]) { g.beginPath(); g.arc(c, c, r, 0, Math.PI * 2); g.stroke(); }
  const colores = ["#f2b705", "#d62f5b", "#1f9d55", "#2b59c3"];
  for (let i = 0; i < 36; i++) {
    const a = (i / 36) * Math.PI * 2;
    g.save();
    g.translate(c + Math.cos(a) * 219, c + Math.sin(a) * 219);
    g.rotate(a);
    g.fillStyle = colores[i % 4];
    g.beginPath(); g.moveTo(0, -11); g.lineTo(9, 0); g.lineTo(0, 11); g.lineTo(-9, 0); g.fill();
    g.restore();
  }
});

const texturaLetrero = () => lienzo(512, 96, (g, w, h) => {
  g.fillStyle = "#7a1f3d";
  g.fillRect(0, 0, w, h);
  g.fillStyle = "#e7b73a";
  g.font = "bold 52px system-ui, sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText("PASEO ARANJUEZ", w / 2, h / 2 + 3);
});

export class Avatar3D {
  constructor(contenedor) {
    this.contenedor = contenedor;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    Object.assign(this.renderer.domElement.style, { width: "100%", height: "100%", display: "block" });
    contenedor.appendChild(this.renderer.domElement);

    this.escena = new THREE.Scene();
    this.camara = new THREE.PerspectiveCamera(28, 1, 0.1, 200);
    this.objetivo = new THREE.Vector3(0, 1.25, 0);
    this.margenes = { arriba: 0, abajo: 0, izquierda: 0, derecha: 0 };

    this.rampa = new THREE.DataTexture(new Uint8Array([105, 170, 225, 255]), 4, 1, THREE.RedFormat);
    this.rampa.minFilter = this.rampa.magFilter = THREE.NearestFilter;
    this.rampa.needsUpdate = true;
    this.matContorno = new THREE.MeshBasicMaterial({ color: 0x1a0f12, side: THREE.BackSide });

    this._estado = "normal";
    this.gestoActual = "normal";
    this.finGesto = 0;
    this.apertura = 0;
    this.ancho = 1;
    this.analizador = null;
    this.simulado = false;
    this.puntero = new THREE.Vector2();
    this.ultimoPuntero = -1e9;
    this.mirada = new THREE.Vector2();
    this.proximoParpadeo = 1500;
    this.parpadeo = -1;
    this.aretes = { angulo: 0, velocidad: 0, giroPrevio: 0 };

    this._construirEscena();
    this._construirPersonaje();

    this.reloj = new THREE.Clock();
    this._redimensionar();
    new ResizeObserver(() => this._redimensionar()).observe(contenedor);
    addEventListener("pointermove", (e) => {
      this.puntero.set((e.clientX / innerWidth) * 2 - 1, -((e.clientY / innerHeight) * 2 - 1));
      this.ultimoPuntero = performance.now();
    });
    this.renderer.setAnimationLoop(() => this._cuadro());
  }

  // ---------- API pública ----------

  get estado() { return this._estado; }
  set estado(valor) { this._estado = COLOR_ESTADO[valor] ? valor : "normal"; }

  gesto(nombre, duracion = 0) {
    this.gestoActual = POSES[nombre] ? nombre : "normal";
    this.finGesto = duracion ? performance.now() + duracion : 0;
  }

  /** Márgenes en px que tapa la interfaz; Paseito se encuadra completa en el espacio libre que queda. */
  encuadre({ arriba = 0, abajo = 0, izquierda = 0, derecha = 0 } = {}) {
    this.margenes = { arriba, abajo, izquierda, derecha };
    this._redimensionar();
  }

  desbloquear() {
    Avatar3D.contextoAudio ??= new (window.AudioContext || window.webkitAudioContext)();
    if (Avatar3D.contextoAudio.state === "suspended") Avatar3D.contextoAudio.resume();
  }

  hablarAudio(url, { alProgresar } = {}) {
    this.desbloquear();
    const ctx = Avatar3D.contextoAudio;
    return new Promise((resolve, reject) => {
      const audio = new Audio(url);
      const analizador = ctx.createAnalyser();
      analizador.fftSize = 512;
      ctx.createMediaElementSource(audio).connect(analizador);
      analizador.connect(ctx.destination);
      this.audio = audio;
      this.analizador = analizador;
      this.buffer = new Uint8Array(analizador.fftSize);
      this.alProgresar = alProgresar;
      const terminar = () => {
        if (this.audio === audio) { this.analizador = null; this.audio = null; this.alProgresar = null; }
        alProgresar?.(1);
        resolve();
      };
      audio.onended = terminar;
      audio.onpause = terminar;
      audio.onerror = reject;
      audio.play().catch(reject);
    });
  }

  hablarSimulado(activo) { this.simulado = activo; }

  callar() {
    if (this.audio) this.audio.pause();
    this.simulado = false;
  }

  // ---------- Construcción ----------

  _toon(color, extra = {}) {
    return new THREE.MeshToonMaterial({ color, gradientMap: this.rampa, ...extra });
  }

  /** Centra la geometría (para que el contorno escalado quede parejo) y la deja en su posición original. */
  _pieza(geo, mat, contorno = 0.025, sombra = true) {
    geo.computeBoundingBox();
    const centro = geo.boundingBox.getCenter(new THREE.Vector3());
    geo.translate(-centro.x, -centro.y, -centro.z);
    const malla = new THREE.Mesh(geo, mat);
    malla.position.copy(centro);
    malla.castShadow = sombra;
    if (contorno) {
      const borde = new THREE.Mesh(geo, this.matContorno);
      borde.scale.setScalar(1 + contorno);
      malla.add(borde);
    }
    return malla;
  }

  _construirEscena() {
    const e = this.escena;
    const azar = aleatorio(11);
    const horizonte = new THREE.Color(0xf7d8ad);

    const cielo = new THREE.Mesh(
      new THREE.SphereGeometry(95, 32, 16),
      new THREE.ShaderMaterial({
        side: THREE.BackSide, depthWrite: false,
        uniforms: {
          cArriba: { value: new THREE.Color(0x2f6fc4) },
          cMedio: { value: new THREE.Color(0x8cc3ec) },
          cHorizonte: { value: horizonte },
        },
        vertexShader: `varying vec3 vDir;
          void main() { vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
        fragmentShader: `uniform vec3 cArriba; uniform vec3 cMedio; uniform vec3 cHorizonte; varying vec3 vDir;
          void main() {
            float h = vDir.y;
            vec3 c = mix(cMedio, cArriba, smoothstep(0.05, 0.6, h));
            c = mix(cHorizonte, c, smoothstep(-0.02, 0.16, h));
            gl_FragColor = vec4(c, 1.0);
            #include <tonemapping_fragment>
            #include <colorspace_fragment>
          }`,
      }),
    );
    e.add(cielo);
    e.fog = new THREE.Fog(horizonte, 22, 80);

    const sol = new THREE.Sprite(new THREE.SpriteMaterial({
      map: texturaRadial(), color: 0xfff1c2, transparent: true, depthWrite: false, fog: false,
    }));
    sol.scale.setScalar(16);
    sol.position.set(20, 22, -62);
    e.add(sol);

    e.add(new THREE.HemisphereLight(0xcfe3ff, 0x6b4a3a, 1.6));
    const luz = new THREE.DirectionalLight(0xfff0d8, 2.6);
    luz.position.set(2.2, 4.2, 3.2);
    luz.castShadow = true;
    luz.shadow.mapSize.set(1024, 1024);
    Object.assign(luz.shadow.camera, { left: -1.6, right: 1.6, top: 2.6, bottom: -0.6, near: 0.5, far: 12 });
    luz.shadow.bias = -0.0008;
    e.add(luz);
    const contraluz = new THREE.DirectionalLight(0xffc27a, 1.8);
    contraluz.position.set(-3, 2.5, -2.5);
    e.add(contraluz);

    // valle: plano con lomas que crecen hacia los costados
    const suelo = new THREE.PlaneGeometry(220, 220, 90, 90);
    const p = suelo.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), y = p.getY(i);
      const d = Math.hypot(x, y);
      const loma = (Math.sin(x * 0.21) * Math.cos(y * 0.17) + Math.sin(x * 0.07 + y * 0.11)) * 1.4;
      p.setZ(i, d > 9 ? loma * Math.min(1, (d - 9) / 25) : 0);
    }
    suelo.computeVertexNormals();
    const valle = new THREE.Mesh(suelo, new THREE.MeshStandardMaterial({ color: 0x8aa35c, flatShading: true, roughness: 1 }));
    valle.rotation.x = -Math.PI / 2;
    valle.position.y = -0.02;
    valle.receiveShadow = true;
    e.add(valle);

    // cordillera del Tunari con nieve en las cumbres
    const matMonte = new THREE.MeshStandardMaterial({ color: 0x77739f, flatShading: true, roughness: 1 });
    const matNieve = new THREE.MeshStandardMaterial({ color: 0xf5f7fc, flatShading: true, roughness: 0.9 });
    for (let i = 0; i < 16; i++) {
      const alto = 9 + azar() * 11;
      const radio = 6 + azar() * 6;
      const lados = 5 + Math.floor(azar() * 3);
      const giro = azar() * Math.PI;
      const x = -46 + i * 6.2 + azar() * 3;
      const z = -46 - azar() * 12;
      const monte = new THREE.Mesh(new THREE.ConeGeometry(radio, alto, lados, 1), matMonte);
      monte.position.set(x, alto / 2 - 1.5, z);
      monte.rotation.y = giro;
      const nieve = new THREE.Mesh(new THREE.ConeGeometry(radio * 0.3, alto * 0.3, lados, 1), matNieve);
      nieve.position.set(x, alto - alto * 0.15 - 1.5 + 0.05, z);
      nieve.rotation.y = giro;
      nieve.scale.setScalar(1.04);
      e.add(monte, nieve);
    }

    // ciudad: casitas y árboles en el valle
    const colores = [0xeedcbc, 0xd9a07a, 0xc77d5a, 0xf3e9d6, 0xe5c79a];
    const geoCasa = new THREE.BoxGeometry(1, 1, 1);
    const geoCopa = new THREE.IcosahedronGeometry(0.55, 0);
    const matCopa = new THREE.MeshStandardMaterial({ color: 0x4f8a3c, flatShading: true });
    for (let i = 0; i < 90; i++) {
      const x = (azar() - 0.5) * 60;
      const z = -9 - azar() * 26;
      if (Math.abs(x) < 3 && z > -14) continue;
      if (i % 3 === 0) {
        const arbol = new THREE.Mesh(geoCopa, matCopa);
        arbol.position.set(x, 0.6 + azar() * 0.3, z);
        arbol.scale.setScalar(0.8 + azar() * 0.7);
        e.add(arbol);
      } else {
        const alto = 0.4 + azar() * 1.1;
        const casa = new THREE.Mesh(geoCasa, new THREE.MeshStandardMaterial({ color: colores[i % colores.length], roughness: 0.9 }));
        casa.scale.set(0.8 + azar() * 1.4, alto, 0.8 + azar() * 1.2);
        casa.position.set(x, alto / 2, z);
        casa.rotation.y = azar() * 0.6;
        e.add(casa);
      }
    }

    // cerro San Pedro con el Cristo de la Concordia
    this.cerro = new THREE.Group();
    const loma = new THREE.Mesh(new THREE.SphereGeometry(4.6, 9, 6), new THREE.MeshStandardMaterial({ color: 0x8f7c52, flatShading: true, roughness: 1 }));
    loma.scale.set(1, 0.55, 1);
    loma.position.y = -0.6;
    const matCristo = new THREE.MeshStandardMaterial({ color: 0xf4f1ea, emissive: 0x3a3630, roughness: 0.6 });
    const cristo = new THREE.Group();
    cristo.add(
      colocar(new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.6, 0.7), matCristo), 0, 0.3, 0),
      colocar(new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.3, 1.6, 8), matCristo), 0, 1.4, 0),
      colocar(new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.16, 0.18), matCristo), 0, 1.95, 0),
      colocar(new THREE.Mesh(new THREE.SphereGeometry(0.15, 12, 8), matCristo), 0, 2.32, 0),
    );
    cristo.position.y = 1.75;
    cristo.scale.setScalar(1.15);
    this.cerro.add(loma, cristo);
    this.cerro.position.set(6, 0, -14);
    e.add(this.cerro);

    // edificio del Paseo Aranjuez
    this.paseo = new THREE.Group();
    const vidrio = new THREE.MeshStandardMaterial({ color: 0x9cc7e0, metalness: 0.35, roughness: 0.2, emissive: 0x1d3a4f });
    const losa = new THREE.MeshStandardMaterial({ color: 0xf2efe8, roughness: 0.7 });
    this.paseo.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(5, 2.7, 2.6), vidrio), 0, 1.35, 0));
    for (const y of [0.05, 0.9, 1.8, 2.7]) {
      this.paseo.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(5.3, 0.12, 2.9), losa), 0, y, 0));
    }
    const letrero = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.6), new THREE.MeshBasicMaterial({ map: texturaLetrero() }));
    letrero.position.set(0, 3.15, 1.0);
    this.paseo.add(letrero);
    this.paseo.position.set(-7, 0, -11);
    this.paseo.rotation.y = 0.35;
    e.add(this.paseo);

    // plataforma con anillo de aguayo y halo que cambia de color según el estado
    const base = new THREE.Mesh(
      new THREE.CylinderGeometry(1.15, 1.25, 0.14, 72),
      new THREE.MeshStandardMaterial({ color: 0x2a0f1b, metalness: 0.45, roughness: 0.35 }),
    );
    base.position.y = -0.07;
    base.receiveShadow = true;
    const tapa = new THREE.Mesh(
      new THREE.CircleGeometry(1.15, 72),
      new THREE.MeshStandardMaterial({ map: texturaPlataforma(), metalness: 0.3, roughness: 0.45 }),
    );
    tapa.rotation.x = -Math.PI / 2;
    tapa.position.y = 0.001;
    tapa.receiveShadow = true;
    this.anillo = new THREE.Mesh(new THREE.TorusGeometry(1.16, 0.018, 8, 120), new THREE.MeshBasicMaterial({ color: C.oro }));
    this.anillo.rotation.x = Math.PI / 2;
    this.halo = new THREE.Mesh(
      new THREE.CircleGeometry(2.1, 64),
      new THREE.MeshBasicMaterial({ map: texturaRadial(), color: C.oro, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false }),
    );
    this.halo.rotation.x = -Math.PI / 2;
    this.halo.position.y = 0.004;
    e.add(base, tapa, this.anillo, this.halo);

    // polvo dorado que sube alrededor
    const cantidad = 260;
    const pos = new Float32Array(cantidad * 3);
    this.velocidades = new Float32Array(cantidad);
    for (let i = 0; i < cantidad; i++) {
      const a = azar() * Math.PI * 2;
      const r = 0.5 + azar() * 1.9;
      pos.set([Math.cos(a) * r, azar() * 2.8, Math.sin(a) * r - 0.3], i * 3);
      this.velocidades[i] = 0.05 + azar() * 0.18;
    }
    const geoPolvo = new THREE.BufferGeometry();
    geoPolvo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    this.polvo = new THREE.Points(geoPolvo, new THREE.PointsMaterial({
      size: 0.035, map: texturaRadial(), color: 0xffd36b, transparent: true, opacity: 0.8,
      blending: THREE.AdditiveBlending, depthWrite: false,
    }));
    e.add(this.polvo);
  }

  _construirPersonaje() {
    const P = (this.personaje = new THREE.Group());
    this.escena.add(P);

    // pollera con tablones
    const geoPollera = new THREE.CylinderGeometry(0.21, 0.44, 0.8, 112, 8, true);
    const p = geoPollera.attributes.position;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
      const t = (0.4 - y) / 0.8;
      const k = 1 + Math.sin(Math.atan2(z, x) * 28) * 0.03 * (0.3 + t);
      p.setXYZ(i, x * k, y, z * k);
    }
    geoPollera.computeVertexNormals();
    geoPollera.translate(0, 0.45, 0);
    P.add(this._pieza(geoPollera, this._toon(C.pollera, { side: THREE.DoubleSide }), 0.02));
    for (const [y, color] of [[0.16, 0x1f9d55], [0.22, 0xf2b705]]) {
      const radio = 0.44 - (y - 0.05) * 0.29;
      const franja = new THREE.Mesh(new THREE.CylinderGeometry(radio + 0.012, radio + 0.014, 0.03, 112, 1, true), this._toon(color, { side: THREE.DoubleSide }));
      franja.position.y = y;
      P.add(franja);
    }

    // parte de arriba (respira)
    const T = (this.torso = new THREE.Group());
    P.add(T);
    const perfilTorso = [[0.2, 0.8], [0.215, 0.92], [0.205, 1.06], [0.18, 1.2], [0.13, 1.31], [0.07, 1.37]];
    T.add(this._pieza(new THREE.LatheGeometry(perfilTorso.map(([r, y]) => new THREE.Vector2(r, y)), 48), this._toon(C.blusa, { side: THREE.DoubleSide }), 0.02));

    // perfil de abajo hacia arriba: si no, las caras miran adentro y el contorno negro tapa la manta
    const perfilManta = [[0.3, 0.97], [0.298, 1.07], [0.285, 1.19], [0.245, 1.29], [0.16, 1.35], [0.075, 1.385]];
    const aguayo = texturaAguayo();
    aguayo.flipY = false;
    this.manta = this._pieza(
      new THREE.LatheGeometry(perfilManta.map(([r, y]) => new THREE.Vector2(r, y)), 72),
      new THREE.MeshToonMaterial({ map: aguayo, gradientMap: this.rampa, side: THREE.DoubleSide }),
      0.02,
    );
    T.add(this.manta);

    const tupu = new THREE.Group();
    tupu.add(new THREE.Mesh(new THREE.SphereGeometry(0.022, 16, 12), this._toon(C.oro)));
    const aguja = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.08, 6), this._toon(0xb8901f));
    aguja.position.y = -0.045;
    tupu.add(aguja);
    tupu.position.set(0, 1.2, 0.29);
    T.add(tupu);

    T.add(this._pieza(new THREE.CylinderGeometry(0.05, 0.056, 0.14, 24).translate(0, 1.41, 0), this._toon(C.pielOscura), 0.03));

    this.brazos = [this._brazo(1), this._brazo(-1)];
    for (const b of this.brazos) T.add(b.hombro);
    this.trenzas = [this._trenza(1), this._trenza(-1)];
    for (const t of this.trenzas) T.add(t);

    this.cabeza = this._cabeza();
    T.add(this.cabeza);
  }

  _brazo(s) {
    const hombro = new THREE.Group();
    hombro.position.set(s * 0.2, 1.27, 0);
    hombro.add(this._pieza(new THREE.CapsuleGeometry(0.042, 0.19, 6, 12).translate(0, -0.12, 0), this._toon(C.blusa), 0.03));
    const codo = new THREE.Group();
    codo.position.y = -0.25;
    codo.add(this._pieza(new THREE.CapsuleGeometry(0.038, 0.17, 6, 12).translate(0, -0.11, 0), this._toon(C.blusa), 0.03));
    const mano = this._pieza(new THREE.SphereGeometry(0.042, 16, 12), this._toon(C.piel), 0.04);
    mano.scale.set(0.8, 1, 0.6);
    mano.position.y = -0.235;
    codo.add(mano);
    hombro.add(codo);
    const pose = POSES.normal(s);
    hombro.rotation.set(pose[0], pose[1], pose[2]);
    codo.rotation.set(pose[3], pose[4], pose[5]);
    return { s, hombro, codo };
  }

  _trenza(s) {
    const grupo = new THREE.Group();
    const curva = new THREE.CatmullRomCurve3([
      [0.12, 1.55, -0.06], [0.17, 1.45, 0.0], [0.22, 1.33, 0.14], [0.235, 1.2, 0.215], [0.225, 1.07, 0.245], [0.21, 0.95, 0.245],
    ].map(([x, y, z]) => new THREE.Vector3(s * x, y, z)));
    const mat = this._toon(C.cabello);
    const geo = new THREE.SphereGeometry(1, 12, 8);
    const arriba = new THREE.Vector3(0, 1, 0);
    const n = 20;
    for (let i = 0; i <= n; i++) {
      const t = i / n;
      const punto = curva.getPoint(t);
      const tangente = curva.getTangent(t);
      const lado = new THREE.Vector3().crossVectors(tangente, new THREE.Vector3(0, 0, 1)).normalize();
      const radio = 0.03 * (1 - 0.35 * t);
      const nudo = new THREE.Mesh(geo, mat);
      nudo.scale.set(radio, radio * 1.7, radio * 0.85);
      nudo.quaternion.setFromUnitVectors(arriba, tangente);
      nudo.position.copy(punto).addScaledVector(lado, (i % 2 ? 1 : -1) * 0.008);
      nudo.castShadow = true;
      grupo.add(nudo);
    }
    const fin = curva.getPoint(1);
    const cordon = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.05, 6), this._toon(0xd62f5b));
    cordon.position.copy(fin).add(new THREE.Vector3(0, -0.035, 0));
    grupo.add(cordon);
    for (const [dx, dy, color] of [[0, -0.07, 0xd62f5b], [-0.018, -0.1, 0xf2b705], [0.018, -0.1, 0x1f9d55]]) {
      const pompon = this._pieza(new THREE.SphereGeometry(0.022, 14, 10), this._toon(color), 0.06);
      pompon.position.copy(fin).add(new THREE.Vector3(dx, dy, 0.01));
      grupo.add(pompon);
    }
    return grupo;
  }

  _cabeza() {
    const pivote = new THREE.Group();
    pivote.position.set(0, 1.45, 0);
    const centro = new THREE.Vector3(0, 0.16, 0);
    const piel = this._toon(C.piel);
    const oscuro = this._toon(0x2a1a14);
    const ref = (this.rostro = {});

    // superficie aproximada de la cara para apoyar los rasgos
    const superficie = (x, y) => 0.15 * Math.sqrt(Math.max(0, 1 - (x / 0.15) ** 2 - (y / 0.168) ** 2));

    // _pieza deja la malla en el centro de su caja; al escalarla hay que escalar también ese corrimiento
    const escalaCabeza = new THREE.Vector3(1, 1.12, 1);
    const sobreCabeza = (malla) => {
      malla.scale.copy(escalaCabeza);
      malla.position.multiply(escalaCabeza).add(centro);
      return malla;
    };
    const cabello = this._toon(C.cabello, { side: THREE.DoubleSide });
    pivote.add(
      sobreCabeza(this._pieza(new THREE.SphereGeometry(0.15, 48, 32), piel, 0.025)),
      sobreCabeza(this._pieza(new THREE.SphereGeometry(0.158, 40, 24, Math.PI / 2 + 0.95, Math.PI * 2 - 1.9, 0, Math.PI * 0.64), cabello, 0.02)),
      sobreCabeza(this._pieza(new THREE.SphereGeometry(0.1585, 40, 12, 0, Math.PI * 2, 0, Math.PI * 0.31), cabello, 0)),
    );

    // ojos
    ref.ojos = [];
    ref.iris = [];
    for (const s of [-1, 1]) {
      const ojo = new THREE.Group();
      ojo.position.set(s * 0.052, centro.y + 0.012, superficie(0.052, 0.012) - 0.008);
      const blanco = new THREE.Mesh(new THREE.SphereGeometry(0.026, 24, 16), this._toon(0xfffaf3));
      blanco.scale.set(1, 0.78, 0.5);
      const iris = new THREE.Group();
      const disco = new THREE.Mesh(new THREE.SphereGeometry(0.015, 20, 14), new THREE.MeshBasicMaterial({ color: 0x3b2416 }));
      disco.scale.set(1, 1, 0.4);
      disco.position.z = 0.011;
      const pupila = new THREE.Mesh(new THREE.SphereGeometry(0.0075, 14, 10), new THREE.MeshBasicMaterial({ color: 0x0d0705 }));
      pupila.scale.set(1, 1, 0.4);
      pupila.position.z = 0.0155;
      const brillo = new THREE.Mesh(new THREE.SphereGeometry(0.0035, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffffff }));
      brillo.position.set(0.005, 0.006, 0.019);
      iris.add(disco, pupila, brillo);
      const pestana = new THREE.Mesh(new THREE.TorusGeometry(0.027, 0.0035, 6, 20, Math.PI), new THREE.MeshBasicMaterial({ color: 0x140c0a }));
      pestana.scale.set(1, 0.8, 1);
      pestana.position.z = 0.008;
      ojo.add(blanco, iris, pestana);
      pivote.add(ojo);
      ref.ojos.push(ojo);
      ref.iris.push(iris);
    }

    // cejas
    ref.cejas = [-1, 1].map((s) => {
      const ceja = new THREE.Mesh(new THREE.CapsuleGeometry(0.0045, 0.032, 4, 8), oscuro);
      ceja.rotation.z = Math.PI / 2 + s * 0.12;
      ceja.position.set(s * 0.055, centro.y + 0.062, superficie(0.055, 0.062) - 0.002);
      ceja.userData.y = ceja.position.y;
      pivote.add(ceja);
      return ceja;
    });

    const nariz = new THREE.Mesh(new THREE.SphereGeometry(0.016, 16, 12), this._toon(C.pielOscura));
    nariz.scale.set(0.9, 1.2, 1);
    nariz.position.set(0, centro.y - 0.028, superficie(0, -0.028) + 0.002);
    pivote.add(nariz);

    for (const s of [-1, 1]) {
      const normal = new THREE.Vector3(s * 0.085, -0.04 / 1.25, superficie(0.085, -0.04)).normalize();
      const mejilla = new THREE.Mesh(new THREE.CircleGeometry(0.026, 24), new THREE.MeshBasicMaterial({ color: 0xe0676a, transparent: true, opacity: 0.35, depthWrite: false }));
      mejilla.position.set(s * 0.085, centro.y - 0.04, superficie(0.085, -0.04) + 0.003);
      mejilla.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
      pivote.add(mejilla);
    }

    // boca: interior, dientes y labios que se mueven con la apertura
    const boca = new THREE.Group();
    boca.position.set(0, centro.y - 0.075, superficie(0, -0.075) - 0.006);
    boca.rotation.x = 0.42;
    ref.interior = new THREE.Mesh(new THREE.SphereGeometry(0.028, 24, 16), new THREE.MeshBasicMaterial({ color: C.boca }));
    ref.dientes = new THREE.Mesh(new THREE.SphereGeometry(0.019, 16, 8), new THREE.MeshBasicMaterial({ color: 0xfbf7f0 }));
    ref.labioSup = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 12), this._toon(C.labio));
    ref.labioInf = new THREE.Mesh(new THREE.SphereGeometry(0.03, 24, 12), this._toon(C.labio));
    ref.labioSup.scale.set(1, 0.2, 0.4);
    ref.labioInf.scale.set(0.95, 0.26, 0.45);
    boca.add(ref.interior, ref.dientes, ref.labioSup, ref.labioInf);
    ref.boca = boca;
    pivote.add(boca);

    // orejas y aretes dorados
    ref.aretes = [];
    for (const s of [-1, 1]) {
      const oreja = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 12), piel);
      oreja.scale.set(0.45, 1, 0.75);
      oreja.position.set(s * 0.149, centro.y, -0.01);
      const arete = new THREE.Group();
      arete.position.set(s * 0.147, centro.y - 0.082, 0.02);
      const aro = new THREE.Mesh(new THREE.TorusGeometry(0.007, 0.0025, 6, 16), this._toon(C.oro));
      const gota = new THREE.Mesh(new THREE.SphereGeometry(0.013, 14, 10), this._toon(C.oro));
      gota.scale.set(1, 1.5, 0.5);
      gota.position.y = -0.03;
      const piedra = new THREE.Mesh(new THREE.SphereGeometry(0.005, 8, 6), new THREE.MeshBasicMaterial({ color: 0xd62f5b }));
      piedra.position.set(0, -0.032, 0.007);
      arete.add(aro, gota, piedra);
      pivote.add(oreja, arete);
      ref.aretes.push(arete);
    }

    // sombrero blanco cochabambino de copa alta con cinta negra
    const sombrero = new THREE.Group();
    sombrero.position.set(0, 0.305, -0.005);
    sombrero.rotation.set(-0.1, 0, 0.06);
    const blanco = this._toon(C.sombrero);
    sombrero.add(this._pieza(new THREE.CylinderGeometry(0.27, 0.27, 0.014, 72), blanco, 0.02));
    sombrero.add(this._pieza(new THREE.CylinderGeometry(0.129, 0.131, 0.045, 64).translate(0, 0.03, 0), this._toon(C.cinta), 0.01));
    sombrero.add(this._pieza(new THREE.CylinderGeometry(0.113, 0.127, 0.23, 64).translate(0, 0.122, 0), blanco, 0.02));
    const copa = this._pieza(new THREE.SphereGeometry(0.113, 48, 8, 0, Math.PI * 2, 0, Math.PI / 2), blanco, 0.02);
    copa.scale.set(1, 0.25, 1);
    copa.position.y = 0.237;
    sombrero.add(copa);
    pivote.add(sombrero);

    return pivote;
  }

  // ---------- Encuadre ----------

  _redimensionar() {
    const w = this.contenedor.clientWidth || innerWidth;
    const h = this.contenedor.clientHeight || innerHeight;
    this.renderer.setSize(w, h, false);
    const cam = this.camara;
    cam.aspect = w / h;
    const tanV = Math.tan(THREE.MathUtils.degToRad(cam.fov / 2));
    const { arriba, abajo, izquierda, derecha } = this.margenes;
    const altoLibre = Math.max(0.3, (h - arriba - abajo) / h);
    const anchoLibre = Math.max(0.3, (w - izquierda - derecha) / w);
    // de la mitad de la pollera (y≈0.45) a la copa del sombrero (y≈2.07), con el brazo en alto para saludar
    this.distancia = Math.max(0.86 / (tanV * altoLibre), 0.52 / (tanV * cam.aspect * anchoLibre));
    const mitad = (prof) => tanV * cam.aspect * (this.distancia + prof);
    this.cerro.position.x = Math.min(7, mitad(14) * 0.6);
    this.paseo.position.x = -Math.min(8.5, mitad(11) * 0.68);
    const dx = (derecha - izquierda) / 2;
    const dy = (abajo - arriba) / 2;
    if (dx || dy) cam.setViewOffset(w, h, dx, dy, w, h);
    else cam.clearViewOffset();
    cam.updateProjectionMatrix();
  }

  // ---------- Animación ----------

  _volumen() {
    this.analizador.getByteTimeDomainData(this.buffer);
    let suma = 0;
    for (const v of this.buffer) suma += ((v - 128) / 128) ** 2;
    return Math.sqrt(suma / this.buffer.length);
  }

  _cuadro() {
    const dt = Math.min(this.reloj.getDelta(), 0.05);
    const t = this.reloj.elapsedTime;
    const ahora = performance.now();
    const suave = (k) => 1 - Math.exp(-dt * k);

    // boca
    let objetivo = 0;
    if (this.analizador) {
      objetivo = Math.min(1, Math.max(0, (this._volumen() - 0.015) * 7));
      if (this.alProgresar && this.audio?.duration) this.alProgresar(this.audio.currentTime / this.audio.duration);
    } else if (this.simulado) {
      objetivo = 0.2 + 0.6 * Math.abs(Math.sin(t * 12.7) * Math.sin(t * 5.3));
    }
    this.apertura += (objetivo - this.apertura) * (objetivo > this.apertura ? 0.5 : 0.25);
    this.ancho += ((objetivo > 0.5 ? 0.88 : 1) + Math.sin(t * 9) * 0.04 * objetivo - this.ancho) * 0.2;
    const habla = Math.min(1, this.apertura * 2.5);
    const r = this.rostro;
    r.boca.scale.x = this.ancho;
    r.interior.scale.set(1, 0.08 + this.apertura * 0.75, 0.35);
    r.interior.position.y = -this.apertura * 0.008;
    r.dientes.scale.set(1, 0.3, 0.3);
    r.dientes.position.set(0, 0.006, 0.004);
    r.dientes.visible = this.apertura > 0.2;
    r.labioSup.position.y = 0.004 + this.apertura * 0.004;
    r.labioInf.position.y = -0.005 - this.apertura * 0.02;

    // parpadeo
    if (ahora > this.proximoParpadeo) { this.parpadeo = ahora; this.proximoParpadeo = ahora + 2200 + Math.random() * 3500; }
    const fase = (ahora - this.parpadeo) / 70;
    const cierre = fase >= 0 && fase < 2 ? 1 - Math.abs(1 - fase) : 0;
    for (const ojo of r.ojos) ojo.scale.y = Math.max(0.08, 1 - cierre);

    // hacia dónde mira: el puntero si se movió hace poco; si no, deambula
    const quieto = ahora - this.ultimoPuntero > 4000;
    const destino = quieto ? new THREE.Vector2(Math.sin(t * 0.23) * 0.4, Math.sin(t * 0.31) * 0.2) : this.puntero;
    this.mirada.lerp(destino, suave(4));
    let giro = this.mirada.x * 0.35;
    let cabeceo = -this.mirada.y * 0.15;
    let inclinacion = Math.sin(t * 0.5) * 0.03;
    if (this._estado === "pensando") { giro = 0.22; cabeceo = -0.16; inclinacion = 0.1; }
    if (this._estado === "escuchando") { inclinacion = 0.09; cabeceo = 0.03; }
    giro += Math.sin(t * 1.7) * 0.05 * habla;
    cabeceo += Math.sin(t * 3.1) * 0.035 * habla;
    inclinacion += Math.sin(t * 2.3) * 0.025 * habla;
    const cab = this.cabeza.rotation;
    cab.y += (giro - cab.y) * suave(5);
    cab.x += (cabeceo - cab.x) * suave(5);
    cab.z += (inclinacion - cab.z) * suave(4);
    const mira = this._estado === "pensando" ? new THREE.Vector2(0.006, 0.006) : new THREE.Vector2(this.mirada.x * 0.006, this.mirada.y * 0.004);
    for (const iris of r.iris) iris.position.set(mira.x, mira.y, 0);

    // cejas: suben al escuchar, al pensar y al enfatizar
    const subir = this._estado === "escuchando" ? 0.01 : this._estado === "pensando" ? 0.007 : this.apertura * 0.005;
    r.cejas.forEach((ceja, i) => {
      const extra = this._estado === "pensando" && i === 1 ? 0.005 : 0;
      ceja.position.y += (ceja.userData.y + subir + extra - ceja.position.y) * suave(8);
    });

    // cuerpo: respiración, leve giro hacia la mirada y vaivén
    this.torso.position.y = Math.sin(t * 1.7) * 0.004;
    this.manta.scale.set(1 + Math.sin(t * 1.7) * 0.006, 1, 1 + Math.sin(t * 1.7) * 0.006);
    this.personaje.rotation.y += (cab.y * 0.25 - this.personaje.rotation.y) * suave(2);
    this.torso.rotation.x += ((this._estado === "escuchando" ? 0.04 : 0) - this.torso.rotation.x) * suave(3);
    for (const [i, trenza] of this.trenzas.entries()) trenza.rotation.z = Math.sin(t * 1.3 + i) * 0.012 - cab.y * 0.03;

    // aretes como péndulos que reaccionan al giro de la cabeza
    const a = this.aretes;
    const velGiro = (cab.y - a.giroPrevio) / Math.max(dt, 1e-3);
    a.giroPrevio = cab.y;
    a.velocidad += (-60 * a.angulo - 4 * a.velocidad - velGiro * 6) * dt;
    a.angulo += a.velocidad * dt;
    for (const arete of r.aretes) arete.rotation.set(a.angulo * 0.5, 0, a.angulo + Math.sin(t * 2) * 0.05);

    // brazos hacia la pose del gesto
    if (this.finGesto && ahora > this.finGesto) { this.gestoActual = "normal"; this.finGesto = 0; }
    for (const b of this.brazos) {
      const pose = POSES[this.gestoActual](b.s);
      if (this.gestoActual === "saludar" && b.s > 0) pose[5] += Math.sin(t * 9) * 0.4;
      const k = suave(6);
      b.hombro.rotation.x += (pose[0] - b.hombro.rotation.x) * k;
      b.hombro.rotation.y += (pose[1] - b.hombro.rotation.y) * k;
      b.hombro.rotation.z += (pose[2] - b.hombro.rotation.z) * k;
      b.codo.rotation.x += (pose[3] - b.codo.rotation.x) * k;
      b.codo.rotation.y += (pose[4] - b.codo.rotation.y) * k;
      b.codo.rotation.z += (pose[5] - b.codo.rotation.z) * k;
    }

    // plataforma: color del estado, pulso con la voz
    const color = new THREE.Color(COLOR_ESTADO[this._estado]);
    this.halo.material.color.lerp(color, suave(4));
    this.anillo.material.color.lerp(color, suave(4));
    this.halo.material.opacity = 0.35 + Math.sin(t * 2.2) * 0.1 + this.apertura * 0.35;
    this.halo.scale.setScalar(1 + this.apertura * 0.08 + (this._estado === "escuchando" ? Math.sin(t * 6) * 0.04 : 0));

    // polvo dorado
    const pos = this.polvo.geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      let y = pos.getY(i) + this.velocidades[i] * dt * (1 + habla);
      if (y > 2.8) y = 0;
      pos.setY(i, y);
    }
    pos.needsUpdate = true;

    // cámara con paralaje suave
    const cam = this.camara;
    const px = this.mirada.x * 0.18;
    const py = this.mirada.y * 0.08;
    cam.position.set(px, this.objetivo.y + 0.1 + py, this.distancia);
    cam.lookAt(this.objetivo);

    this.renderer.render(this.escena, cam);
  }
}
