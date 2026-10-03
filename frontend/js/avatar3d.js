// Paseito en 3D (Three.js): cochabambina con sombrero blanco de copa alta, trenzas con tullmas,
// manta de aguayo y pollera, sobre una plataforma frente al Tunari y el Cristo de la Concordia.
// Misma API que el avatar 2D (avatar.js) para poder intercambiarlos:
//
//   const avatar = new Avatar3D(contenedor, { calidadAdaptativa: true });  // lanza un error si no hay WebGL
//   avatar.desbloquear();                        // dentro de un clic (política de audio)
//   await avatar.hablarAudio(url, { alProgresar: f => ..., texto: "lo que dice el audio" });  // texto: boca por visemas
//   avatar.hablarSimulado(true / false);         // voz del navegador; avatar.decirPalabra(p) en cada palabra
//   avatar.estado = "normal" | "escuchando" | "pensando";
//   avatar.gesto("saludar" | "despedir" | "presentar" | "pensar" | "normal", ms);
//   avatar.señalar(x, y, ms);  avatar.mirarA(x, y, ms);   // punto de la pantalla en px
//   avatar.asentir();  avatar.sonreir(intensidad, ms);
//   avatar.encuadre({ arriba, abajo, izquierda, derecha });  // px que tapa la interfaz

import * as THREE from "three";
import { EffectComposer } from "https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/postprocessing/RenderPass.js";
import { BokehPass } from "https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/postprocessing/BokehPass.js";
import { OutputPass } from "https://cdn.jsdelivr.net/npm/three@0.186.1/examples/jsm/postprocessing/OutputPass.js";
import { FORMAS, formaEn, formaPorVolumen, palabraEn, planDePalabra, prepararPlan } from "./habla.js";
import { crearCristoGLB } from './cristoGLB.js';
import { crearEdificioGLB } from './edificioGLB.js';
import { crearArboles } from './arbolesGLB.js';

const C = {
  piel: 0xc68a5c, pielOscura: 0xa96f46, cabello: 0x1e1412, sombrero: 0xf7f3ea, cinta: 0x151515,
  blusa: 0xfbf7ef, pollera: 0xc2185b, oro: 0xe7b73a, labio: 0xb4505a, labioSup: 0xa3434d, boca: 0x3a0d12,
  lengua: 0xc65a63, manta: 0xb03a63,
};
const COLOR_ESTADO = { normal: 0xe7b73a, escuchando: 0xff5470, pensando: 0x8f7bff };
const CLAVES_BOCA = Object.keys(FORMAS.reposo);
const CIELO = {
  arriba: { noche: new THREE.Color(0x07132e), dia: new THREE.Color(0x2f6fc4), dorado: new THREE.Color(0x421c4c) },
  medio: { noche: new THREE.Color(0x20385e), dia: new THREE.Color(0x8cc3ec), dorado: new THREE.Color(0xd06b5d) },
  horizonte: { noche: new THREE.Color(0x514766), dia: new THREE.Color(0xf7d8ad), dorado: new THREE.Color(0xf2a45e) },
};

// Pose de cada brazo en coordenadas del torso: adónde va la mano, hacia dónde apunta el codo, la forma
// de los dedos y el giro de la mano sobre el antebrazo. s = +1 brazo izquierdo de Paseito (derecha de la pantalla).
const POSES = {
  normal: (s) => ({ mano: [s * 0.05, 0.83, 0.3], codo: [s, -0.4, -0.45], dedos: "relajada", giro: -s * 1.2 }),
  saludar: (s) => (s > 0 ? { mano: [0.42, 1.62, 0.16], codo: [1, -0.8, -0.1], dedos: "abierta", giro: Math.PI, ola: 9 } : POSES.normal(s)),
  despedir: (s) => (s > 0 ? { mano: [0.44, 1.6, 0.2], codo: [1, -0.8, -0.1], dedos: "abierta", giro: Math.PI, ola: 6 } : POSES.normal(s)),
  presentar: (s) => (s > 0 ? { mano: [0.48, 1.03, 0.28], codo: [0.5, -1, -0.4], dedos: "abierta", giro: -1.2 } : POSES.normal(s)),
  pensar: (s) => (s < 0 ? { mano: [-0.04, 1.47, 0.2], codo: [-0.4, -1, 0.15], dedos: "barbilla", giro: Math.PI } : POSES.normal(s)),
  trenza: (s) => (s > 0 ? { mano: [0.19, 1.12, 0.3], codo: [1, -0.7, -0.2], dedos: "pinza", giro: 1.6 } : POSES.normal(s)),
  sombrero: (s) => (s < 0 ? { mano: [-0.2, 1.69, 0.17], codo: [-1, -0.25, 0.1], dedos: "pinza", giro: Math.PI } : POSES.normal(s)),
};
// Se precalculan para no crear objetos en cada cuadro.
const POSES_LADO = Object.fromEntries(Object.entries(POSES).map(([nombre, fn]) => [nombre, [-1, 1].map((s) => {
  const p = fn(s);
  return { mano: new THREE.Vector3(...p.mano), codo: new THREE.Vector3(...p.codo), dedos: p.dedos, giro: p.giro, ola: p.ola || 0 };
})]));
const GESTOS = new Set([...Object.keys(POSES), "señalar"]);
// Curvatura de cada dedo (índice, medio, anular, meñique), del pulgar y separación entre dedos.
const MANOS = {
  relajada: { curva: [0.45, 0.55, 0.62, 0.7], pulgar: 0.35, abre: 0.05 },
  abierta: { curva: [0.05, 0.03, 0.05, 0.09], pulgar: 0.05, abre: 0.17 },
  señalar: { curva: [0, 1.45, 1.55, 1.6], pulgar: 0.95, abre: 0 },
  barbilla: { curva: [0.85, 1.05, 1.15, 1.2], pulgar: 0.6, abre: 0 },
  pinza: { curva: [0.5, 0.8, 0.95, 1.05], pulgar: 0.55, abre: 0.02 },
};
const ABAJO = new THREE.Vector3(0, -1, 0);
const tmp = {
  a: new THREE.Vector3(), b: new THREE.Vector3(), c: new THREE.Vector3(), d: new THREE.Vector3(), q: new THREE.Quaternion(),
  mano: new THREE.Vector3(), polo: new THREE.Vector3(), v2: new THREE.Vector2(), m: new THREE.Matrix4(), color: new THREE.Color(),
};
const limitar = THREE.MathUtils.clamp;

/** Resorte amortiguado (estado {x, v}) que persigue a `objetivo`: da el retraso y el vaivén de telas y trenzas. */
function resorte(e, objetivo, dt, rigidez, amortiguacion) {
  e.v += ((objetivo - e.x) * rigidez - e.v * amortiguacion) * dt;
  e.x += e.v * dt;
}

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

const texturaValle = () => {
  const textura = lienzo(512, 512, (g, w, h) => {
    g.fillStyle = "#71894f";
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 1800; i++) {
      const x = (i * 197) % w;
      const y = (i * 317) % h;
      const tono = i % 5 === 0 ? "rgba(46,70,38,.18)" : "rgba(190,170,94,.13)";
      g.fillStyle = tono;
      g.fillRect(x, y, 2 + (i % 4), 1 + (i % 3));
    }
    g.strokeStyle = "rgba(37,65,38,.18)";
    g.lineWidth = 2;
    for (let y = 18; y < h; y += 27) {
      g.beginPath();
      g.moveTo(0, y);
      g.quadraticCurveTo(w * 0.45, y - 8, w, y + 5);
      g.stroke();
    }
  });
  textura.wrapS = textura.wrapT = THREE.RepeatWrapping;
  textura.repeat.set(14, 14);
  return textura;
};

/**
 * Cristo de la Concordia con sus proporciones reales (1 unidad = 10 m): imagen de 3,42 sobre pedestal de 0,62,
 * 3,29 entre las manos y cabeza de 0,46. Túnica con pliegues, manto cruzado al pecho, mangas anchas que cuelgan
 * bajo los antebrazos, cabeza levemente inclinada hacia la ciudad y pedestal redondo escalonado con la cruz.
 */
function crearCristo() {
  const mat = new THREE.MeshStandardMaterial({ color: 0xf4f0e6, emissive: 0x403c34, roughness: 0.6, side: THREE.DoubleSide });
  const sombreado = new THREE.MeshStandardMaterial({ color: 0xd9d2c4, emissive: 0x2a2620, roughness: 0.7, side: THREE.DoubleSide });
  const cristo = new THREE.Group();

  for (const [r, alto, y] of [[0.56, 0.24, 0.12], [0.48, 0.22, 0.35], [0.41, 0.16, 0.54]]) {
    cristo.add(colocar(new THREE.Mesh(new THREE.CylinderGeometry(r, r * 1.03, alto, 40), mat), 0, y, 0));
  }
  cristo.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.17, 0.02), sombreado), 0, 0.36, 0.49));
  cristo.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.032, 0.02), sombreado), 0, 0.395, 0.49));

  const cuerpo = new THREE.Group();
  cuerpo.position.y = 0.62;
  cristo.add(cuerpo);

  // túnica: más ancha en el ruedo, pliegues verticales hasta el pecho
  const tunica = new THREE.LatheGeometry(
    [[0.38, 0], [0.32, 0.14], [0.28, 0.7], [0.26, 1.4], [0.27, 2.0], [0.3, 2.45], [0.33, 2.66], [0.24, 2.78], [0.1, 2.84]]
      .map(([r, y]) => new THREE.Vector2(r, y)), 48,
  );
  const pt = tunica.attributes.position;
  for (let i = 0; i < pt.count; i++) {
    const y = pt.getY(i);
    if (y > 2.4) continue;
    const k = 1 + Math.sin(Math.atan2(pt.getZ(i), pt.getX(i)) * 14) * 0.03 * (1 - y / 2.4);
    pt.setXYZ(i, pt.getX(i) * k, y, pt.getZ(i) * k);
  }
  tunica.computeVertexNormals();
  const malla = new THREE.Mesh(tunica, mat);
  malla.scale.z = 0.72;
  cuerpo.add(malla);

  // capa sobre los hombros, bordes de la túnica al frente y el manto cruzado sobre el pecho
  const capa = new THREE.Mesh(
    new THREE.LatheGeometry([[0.31, 2.2], [0.34, 2.48], [0.355, 2.64], [0.27, 2.77], [0.12, 2.83]].map(([r, y]) => new THREE.Vector2(r, y)), 40),
    mat,
  );
  capa.scale.z = 0.76;
  cuerpo.add(capa);
  for (const s of [-1, 1]) {
    const borde = new THREE.Mesh(new THREE.CapsuleGeometry(0.018, 1.75, 4, 8), sombreado);
    borde.position.set(s * 0.1, 1.25, 0.2);
    borde.rotation.z = s * 0.03;
    cuerpo.add(borde);
  }
  const banda = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.15, 0.02), sombreado);
  banda.position.set(0.02, 2.33, 0.228);
  banda.rotation.z = -0.48;
  cuerpo.add(banda);

  // brazos abiertos, apenas levantados, con la manga ancha que cae bajo el antebrazo
  const caida = new THREE.Shape();
  caida.moveTo(0, 0);
  caida.lineTo(1.22, 0);
  caida.quadraticCurveTo(1.27, -0.2, 1.2, -0.4);
  caida.quadraticCurveTo(0.98, -0.47, 0.74, -0.37);
  caida.quadraticCurveTo(0.6, -0.2, 0.42, -0.16);
  caida.quadraticCurveTo(0.12, -0.22, 0, -0.52);
  caida.closePath();
  const geoManga = new THREE.ExtrudeGeometry(caida, {
    depth: 0.08, bevelEnabled: true, bevelThickness: 0.03, bevelSize: 0.025, bevelSegments: 3, curveSegments: 10,
  }).translate(0, -0.04, -0.04);
  for (const s of [-1, 1]) {
    const brazo = new THREE.Group();
    brazo.position.set(s * 0.26, 2.62, 0);
    brazo.rotation.z = s * 0.07;
    brazo.scale.x = s;
    brazo.add(colocar(new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.14, 1.3, 16).rotateZ(-Math.PI / 2), mat), 0.62, 0, 0));
    brazo.add(colocar(new THREE.Mesh(new THREE.SphereGeometry(0.14, 16, 12), mat), 0, 0, 0));
    brazo.add(new THREE.Mesh(geoManga, mat));
    const puno = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.08, 0.08, 14).rotateZ(-Math.PI / 2), mat);
    puno.position.x = 1.29;
    const palma = new THREE.Mesh(new THREE.SphereGeometry(1, 18, 12), mat);
    palma.scale.set(0.11, 0.05, 0.09);
    palma.position.set(1.4, 0.01, 0.01);
    const dedos = new THREE.Mesh(new THREE.CapsuleGeometry(0.045, 0.1, 4, 10).rotateZ(-Math.PI / 2), mat);
    dedos.scale.set(1, 0.85, 1.5);
    dedos.position.set(1.52, 0.035, 0.005);
    dedos.rotation.z = 0.25;
    const pulgar = new THREE.Mesh(new THREE.CapsuleGeometry(0.025, 0.07, 4, 8).rotateX(Math.PI / 2), mat);
    pulgar.position.set(1.38, 0.03, 0.1);
    pulgar.rotation.y = -0.5;
    brazo.add(puno, palma, dedos, pulgar);
    cuerpo.add(brazo);
  }

  // cabeza con cabello largo hasta los hombros y barba, mirando un poco hacia abajo, a la ciudad
  cuerpo.add(colocar(new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.11, 0.16, 16), mat), 0, 2.86, 0));
  const cabeza = new THREE.Group();
  cabeza.position.set(0, 3.1, 0.02);
  cabeza.rotation.x = 0.2;
  const craneo = new THREE.Mesh(new THREE.SphereGeometry(0.19, 28, 20), mat);
  craneo.scale.set(0.9, 1.18, 0.98);
  const cabello = new THREE.Mesh(new THREE.SphereGeometry(0.2, 28, 20, Math.PI / 2 + 0.9, Math.PI * 2 - 1.8, 0, Math.PI * 0.62), sombreado);
  cabello.scale.set(0.95, 1.18, 1);
  const melena = new THREE.Mesh(new THREE.CapsuleGeometry(0.14, 0.24, 6, 16), sombreado);
  melena.scale.set(1.35, 1, 0.55);
  melena.position.set(0, -0.2, -0.08);
  const barba = new THREE.Mesh(new THREE.SphereGeometry(0.1, 18, 12, 0, Math.PI * 2, Math.PI * 0.35, Math.PI * 0.65), sombreado);
  barba.scale.set(1, 1.15, 0.85);
  barba.position.set(0, -0.1, 0.07);
  const nariz = new THREE.Mesh(new THREE.ConeGeometry(0.025, 0.07, 8), sombreado);
  nariz.rotation.x = 0.35;
  nariz.position.set(0, 0, 0.18);
  cabeza.add(melena, craneo, cabello, barba, nariz);
  cuerpo.add(cabeza);
  return cristo;
}

const texturaLetrero = () => lienzo(512, 96, (g, w, h) => {
  g.fillStyle = "#7a1f3d";
  g.fillRect(0, 0, w, h);
  g.fillStyle = "#e7b73a";
  g.font = "bold 52px system-ui, sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText("PASEO ARANJUEZ", w / 2, h / 2 + 3);
});

// Iris café con anillo oscuro, vetas claras y pupila.
const texturaIris = () => lienzo(128, 128, (g, w) => {
  const c = w / 2;
  const r = g.createRadialGradient(c, c, 0, c, c, c);
  r.addColorStop(0, "#120904"); r.addColorStop(0.38, "#120904"); r.addColorStop(0.42, "#5a3317");
  r.addColorStop(0.68, "#8d5a2b"); r.addColorStop(0.88, "#55301a"); r.addColorStop(1, "#24130a");
  g.fillStyle = r;
  g.fillRect(0, 0, w, w);
  g.strokeStyle = "rgba(255, 214, 160, .22)";
  g.lineWidth = 2;
  for (let i = 0; i < 28; i++) {
    const a = (i / 28) * Math.PI * 2;
    g.beginPath();
    g.moveTo(c + Math.cos(a) * c * 0.45, c + Math.sin(a) * c * 0.45);
    g.lineTo(c + Math.cos(a) * c * 0.82, c + Math.sin(a) * c * 0.82);
    g.stroke();
  }
});

/**
 * Boca de dibujo animado que se deforma en cada cuadro (sin crear geometría nueva): labios, interior,
 * dientes y lengua son tiras de vértices fijos que siguen la forma del visema y la sonrisa.
 */
const COLUMNAS_BOCA = 17;
class BocaFlexible {
  constructor(materiales) {
    this.grupo = new THREE.Group();
    this.tiras = {};
    for (const [nombre, orden] of [["interior", 0], ["lengua", 1], ["dientes", 2], ["labioInf", 3], ["labioSup", 3]]) {
      const geo = new THREE.BufferGeometry();
      const n = COLUMNAS_BOCA * 2;
      geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(n * 3), 3).setUsage(THREE.DynamicDrawUsage));
      const normales = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) normales[i * 3 + 2] = 1;
      geo.setAttribute("normal", new THREE.BufferAttribute(normales, 3));
      const indices = [];
      for (let i = 0; i < COLUMNAS_BOCA - 1; i++) {
        const a = i * 2;
        indices.push(a, a + 1, a + 2, a + 2, a + 1, a + 3);
      }
      geo.setIndex(indices);
      const malla = new THREE.Mesh(geo, materiales[nombre]);
      malla.frustumCulled = false;
      malla.renderOrder = orden;
      this.grupo.add(malla);
      this.tiras[nombre] = geo.attributes.position;
    }
  }

  /** b: forma actual (abre, ancho, redondo, presion, dientes); sonrisa 0-1. */
  actualizar(b, sonrisa) {
    const abre = Math.max(0, b.abre), red = b.redondo, pres = b.presion;
    const w = 0.028 * b.ancho * (1 - 0.28 * red) * (1 + 0.1 * sonrisa);
    const expo = 0.45 + 0.4 * (1 - red);
    const aSup = abre * (0.0055 + 0.004 * red);
    const aInf = abre * (0.019 + 0.002 * red);
    const levanta = sonrisa * 0.0085 * (1 - 0.5 * abre) * (1 - red);
    const tSup = 0.0047 * (1 - 0.3 * pres) + 0.0014 * red;
    const tInf = 0.0064 * (1 - 0.25 * pres) + 0.0014 * red;
    const alto = 0.006 * (0.45 + 0.55 * b.dientes);
    const f = (u) => Math.pow(Math.max(0, 1 - u * u), expo);
    const grosor = (u) => Math.pow(Math.max(0, 1 - u * u), 0.35);
    const linea = (u) => levanta * u * u - sonrisa * 0.0015;
    const sup = (u) => linea(u) + aSup * f(u);
    const inf = (u) => linea(u) - aInf * f(u);
    const arco = (u) => 0.0007 * Math.exp(-(((Math.abs(u) - 0.3) / 0.16) ** 2)) - 0.0004 * Math.exp(-((u / 0.1) ** 2));
    // la cara es curva: los bordes se hunden hacia atrás y hacia abajo
    const z = (x, y, encima) => encima - (x * x) / (2 * 0.134) - (y * y) / (2 * 0.2);
    const sobresale = (u) => 0.0032 * red * f(u) + 0.0008 * pres;
    const { interior, lengua, dientes, labioSup, labioInf } = this.tiras;
    for (let i = 0; i < COLUMNAS_BOCA; i++) {
      const u = -1 + (2 * i) / (COLUMNAS_BOCA - 1);
      const x = u * w;
      const yS = sup(u), yI = inf(u);
      const zLabio = sobresale(u);
      labioSup.setXYZ(i * 2, x, yS + tSup * grosor(u) + arco(u), z(x, yS, 0.0038 + zLabio));
      labioSup.setXYZ(i * 2 + 1, x, yS, z(x, yS, 0.0038 + zLabio));
      labioInf.setXYZ(i * 2, x, yI, z(x, yI, 0.0038 + zLabio));
      labioInf.setXYZ(i * 2 + 1, x, yI - tInf * grosor(u), z(x, yI, 0.0038 + zLabio));
      interior.setXYZ(i * 2, x * 1.02, yS + 0.0004, z(x, yS, 0.0022));
      interior.setXYZ(i * 2 + 1, x * 1.02, yI - 0.0004, z(x, yI, 0.0022));
      const ud = u * 0.8, xd = ud * w;
      const dSup = sup(ud), dInf = inf(ud);
      dientes.setXYZ(i * 2, xd, dSup + 0.0003, z(xd, dSup, 0.003));
      dientes.setXYZ(i * 2 + 1, xd, Math.max(dSup - alto * Math.pow(1 - ud * ud, 0.25), dInf), z(xd, dSup, 0.003));
      const ul = u * 0.62, xl = ul * w;
      const lInf = inf(ul);
      lengua.setXYZ(i * 2, xl, Math.min(lInf + 0.0065 * f(ul), sup(ul)), z(xl, lInf, 0.0026));
      lengua.setXYZ(i * 2 + 1, xl, lInf + 0.0002, z(xl, lInf, 0.0026));
    }
    for (const tira of Object.values(this.tiras)) tira.needsUpdate = true;
  }
}

export class Avatar3D {
  constructor(contenedor, { calidadAdaptativa = true } = {}) {
    this.contenedor = contenedor;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    // Si el equipo no llega a ~40 cuadros por segundo se baja la resolución interna (y se recupera si sobra).
    this.calidad = {
      activa: calidadAdaptativa, maxima: Math.min(devicePixelRatio, 2), minima: Math.min(devicePixelRatio, 2) * 0.6,
      suma: 0, cuadros: 0, ultimoCambio: 0,
    };
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
    this.analizador = null;
    this.simulado = false;
    this.plan = null;
    this.palabraSim = null;
    this.boca = { ...FORMAS.reposo };
    this._forma = { ...FORMAS.reposo };
    this.sonrisa = 0.3;
    this.intensidadSonrisa = 0;
    this.finSonrisa = 0;
    this.puntero = new THREE.Vector2();
    this.ultimoPuntero = -1e9;
    this.mirada = new THREE.Vector2();
    this.puntoMirada = new THREE.Vector2();
    this.mirarHasta = 0;
    this.cabezaBase = { x: 0, y: 0, z: 0 };
    this.asentirDesde = -1e9;
    this.sorpresaHasta = 0;
    this.inclinacionExtra = 0;
    this.inclinarHasta = 0;
    this.proximoParpadeo = 1500;
    this.parpadeo = -1;
    this.parpado = { sup: -1.02, inf: 0.95 };
    this.cejas = { subir: [0, 0], interior: [0, 0] };
    this.aretes = { angulo: 0, velocidad: 0, giroPrevio: 0 };
    this.cadera = 0;
    this.pesoObjetivo = 0;
    this.suspiroDesde = -1e9;
    this.proximoReposo = performance.now() + 5000;
    this.ultimaAccion = "";
    this.señal = { s: 1, mano: new THREE.Vector3() };
    this.raycaster = new THREE.Raycaster();
    this.planoSeñal = new THREE.Plane(new THREE.Vector3(0, 0, 1), -0.5);
    this.fisica = {
      giroPrevio: 0, caderaPrevia: 0, cabezaPrevia: 0,
      polleraGiro: { x: 0, v: 0 }, polleraX: { x: 0, v: 0 }, polleraZ: { x: 0, v: 0 },
    };
    this.ultimaHoraDia = -1;

    this._construirEscena();
    this._construirPersonaje();
    this.personaje.traverse((objeto) => objeto.layers.set(1));
    this.escena.traverse((objeto) => {
      if (objeto.isLight) objeto.layers.enable(1);
    });
    this.compositor = new EffectComposer(this.renderer);
    this.compositor.addPass(new RenderPass(this.escena, this.camara));
    this.desenfoque = new BokehPass(this.escena, this.camara, {
      focus: 3.5,
      aperture: 0.006,
      maxblur: 0.006,
    });
    this.compositor.addPass(this.desenfoque);
    this.compositor.addPass(new OutputPass());

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
    this.gestoActual = GESTOS.has(nombre) ? nombre : "normal";
    this.finGesto = duracion ? performance.now() + duracion : 0;
  }

  /** Señala con el índice y mira un punto de la pantalla (px), p. ej. las tarjetas de resultados. */
  señalar(x, y, duracion = 2600) {
    this._aPantalla(x, y, tmp.v2);
    this.raycaster.setFromCamera(tmp.v2, this.camara);
    const punto = this.raycaster.ray.intersectPlane(this.planoSeñal, tmp.a);
    if (!punto) return;
    this.torso.updateWorldMatrix(true, false);
    const local = this.torso.worldToLocal(punto);
    const s = local.x >= 0 ? 1 : -1;
    const hombro = tmp.b.set(s * 0.245, 1.255, 0.01);
    const direccion = tmp.c.subVectors(local, hombro).normalize();
    const mano = this.señal.mano.copy(hombro).addScaledVector(direccion, 0.47);
    mano.set(limitar(mano.x, -0.62, 0.62), limitar(mano.y, 1.0, 1.72), Math.max(mano.z, 0.14));
    this.señal.s = s;
    this.gesto("señalar", duracion);
    this.mirarA(x, y, Math.min(duracion, 1600));
  }

  /** Mira un punto de la pantalla (px) durante `duracion` ms. */
  mirarA(x, y, duracion = 1500) {
    this._aPantalla(x, y, this.puntoMirada);
    this.mirarHasta = performance.now() + duracion;
  }

  /** Dos cabeceos cortos, como quien escucha y dice "ajá". */
  asentir() {
    const ahora = performance.now();
    if (ahora - this.asentirDesde > 900) this.asentirDesde = ahora;
  }

  sonreir(intensidad = 1, duracion = 2500) {
    this.intensidadSonrisa = intensidad;
    this.finSonrisa = performance.now() + duracion;
  }

  _aPantalla(x, y, salida) {
    const r = this.renderer.domElement.getBoundingClientRect();
    return salida.set(((x - r.left) / r.width) * 2 - 1, -(((y - r.top) / r.height) * 2 - 1));
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

  /**
   * Reproduce un audio (URL) moviendo la boca. Con `texto` (lo que dice el audio) la boca toma la forma de
   * cada sonido y `alProgresar` avanza palabra por palabra; sin texto, la boca sigue solo el volumen.
   */
  hablarAudio(url, { alProgresar, texto } = {}) {
    this.desbloquear();
    const ctx = Avatar3D.contextoAudio;
    const plan = texto ? prepararPlan(url, texto, ctx).catch(() => null) : Promise.resolve(null);
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
      this.plan = null;
      this.ultimaPalabra = -2;
      let hecho = false;
      const terminar = () => {
        if (hecho) return;
        hecho = true;
        if (this.audio === audio) { this.analizador = null; this.audio = null; this.alProgresar = null; this.plan = null; }
        if (this._terminar === terminar) this._terminar = null;
        alProgresar?.(1);
        resolve();
      };
      this._terminar = terminar;
      audio.onended = terminar;
      audio.onpause = terminar;
      audio.onerror = reject;
      // El análisis del audio tarda unos milisegundos; si se demora, empieza a hablar igual y se suma al llegar.
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

  /** Con la voz del navegador: forma de boca de la palabra que empieza a sonar (evento onboundary). */
  decirPalabra(palabra) {
    if (palabra) this.palabraSim = { plan: planDePalabra(palabra), desde: performance.now() };
  }

  callar() {
    const hablaba = !!(this.audio || this.simulado);
    if (this.audio) this.audio.pause();
    this._terminar?.();
    this.simulado = false;
    this.palabraSim = null;
    this.plan = null;
    if (hablaba) this.sorpresaHasta = performance.now() + 450;
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

    const materialCielo = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false,
      uniforms: {
        cArriba: { value: CIELO.arriba.dia.clone() },
        cMedio: { value: CIELO.medio.dia.clone() },
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
    });
    this.materialCielo = materialCielo;
    const cielo = new THREE.Mesh(new THREE.SphereGeometry(95, 32, 16), materialCielo);
    e.add(cielo);
    e.fog = new THREE.Fog(horizonte, 22, 80);

    const sol = new THREE.Sprite(new THREE.SpriteMaterial({
      map: texturaRadial(), color: 0xfff1c2, transparent: true, depthWrite: false, fog: false,
    }));
    sol.scale.setScalar(16);
    sol.position.set(20, 22, -62);
    this.sol = sol;
    e.add(sol);

    this.luzCielo = new THREE.HemisphereLight(0xcfe3ff, 0x6b4a3a, 1.35);
    e.add(this.luzCielo);
    const luz = this.luzPrincipal = new THREE.DirectionalLight(0xffedcf, 2.8);
    luz.position.set(2.2, 4.2, 3.2);
    luz.castShadow = true;
    luz.shadow.mapSize.set(1024, 1024);
    Object.assign(luz.shadow.camera, { left: -1.6, right: 1.6, top: 2.6, bottom: -0.6, near: 0.5, far: 12 });
    luz.shadow.bias = -0.0008;
    luz.shadow.normalBias = 0.018;
    luz.shadow.radius = 2;
    e.add(luz);
    const relleno = this.luzRelleno = new THREE.DirectionalLight(0x9bc8ff, 0.75);
    relleno.position.set(-4, 3.2, 4.5);
    e.add(relleno);
    const contraluz = this.luzContraluz = new THREE.DirectionalLight(0xffb36b, 1.25);
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
    const valle = new THREE.Mesh(suelo, new THREE.MeshStandardMaterial({ map: texturaValle(), color: 0xb3b878, flatShading: true, roughness: 1 }));
    valle.rotation.x = -Math.PI / 2;
    valle.position.y = -0.02;
    valle.receiveShadow = true;
    e.add(valle);

    // Montes, casas, techos y árboles se dibujan instanciados: una llamada de dibujo por tipo en vez de una por objeto.
    const matriz = new THREE.Matrix4();
    const giroY = new THREE.Quaternion();
    const posicion = new THREE.Vector3();
    const escala = new THREE.Vector3();
    const color = new THREE.Color();
    const rotarY = (angulo) => giroY.setFromAxisAngle(new THREE.Vector3(0, 1, 0), angulo);

    // cordillera del Tunari con nieve en las cumbres
    const matMonte = new THREE.MeshStandardMaterial({ color: 0x77739f, flatShading: true, roughness: 1 });
    const matNieve = new THREE.MeshStandardMaterial({ color: 0xf5f7fc, flatShading: true, roughness: 0.9 });
    const montesPorLados = { 5: [], 6: [], 7: [] };
    for (let i = 0; i < 16; i++) {
      const alto = 9 + azar() * 11;
      const radio = 6 + azar() * 6;
      const lados = 5 + Math.floor(azar() * 3);
      const giro = azar() * Math.PI;
      const x = -46 + i * 6.2 + azar() * 3;
      const z = -46 - azar() * 12;
      montesPorLados[lados].push({ alto, radio, giro, x, z });
    }
    for (const [lados, montes] of Object.entries(montesPorLados)) {
      if (!montes.length) continue;
      const roca = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, Number(lados), 1), matMonte, montes.length);
      const nieve = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, Number(lados), 1), matNieve, montes.length);
      montes.forEach((m, i) => {
        rotarY(m.giro);
        roca.setMatrixAt(i, matriz.compose(posicion.set(m.x, m.alto / 2 - 1.5, m.z), giroY, escala.set(m.radio, m.alto, m.radio)));
        const k = 0.3 * 1.04;
        nieve.setMatrixAt(i, matriz.compose(posicion.set(m.x, m.alto - m.alto * 0.15 - 1.5 + 0.05, m.z), giroY, escala.set(m.radio * k, m.alto * k, m.radio * k)));
      });
      e.add(roca, nieve);
    }

    // el Tunari: el pico nevado que domina el valle
    const tunari = new THREE.Group();
    tunari.add(colocar(new THREE.Mesh(new THREE.ConeGeometry(17, 27, 7, 1), matMonte), 0, 12, 0));
    const cumbre = new THREE.Mesh(new THREE.ConeGeometry(6.4, 10.2, 7, 1), matNieve);
    cumbre.position.y = 21;
    cumbre.scale.setScalar(1.03);
    tunari.add(cumbre);
    tunari.position.set(-14, -1.5, -64);
    tunari.rotation.y = 0.4;
    e.add(tunari);

    // ciudad jardín: casitas con techo de teja, jacarandás morados y molles
    const colores = [0xf3e9d6, 0xeedcbc, 0xe5c79a, 0xf6efe2, 0xd9a07a];
    const geoCasa = new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0);
    const geoTecho = new THREE.ConeGeometry(0.78, 0.42, 4).rotateY(Math.PI / 4).translate(0, 1.21, 0);
    const matTeja = new THREE.MeshStandardMaterial({ color: 0xb4532f, flatShading: true, roughness: 0.9 });
    const geoCopa = new THREE.IcosahedronGeometry(0.55, 0);
    const coloresCopas = [0x9b72d9, 0x4f8a3c, 0xb08ae6, 0x6c9a45];
    const matCopa = new THREE.MeshStandardMaterial({ flatShading: true });
    const casas = [];
    const arboles = [];
    for (let i = 0; i < 130; i++) {
      const x = (azar() - 0.5) * 64;
      const z = -8 - azar() * 30;
      if (Math.abs(x) < 6 && z > -16) continue;
      if (i % 3 === 0) {
        const y = 0.6 + azar() * 0.3;
        arboles.push({ color: coloresCopas[i % coloresCopas.length], x, y, z, s: 0.8 + azar() * 0.7 });
      } else {
        const sx = 0.8 + azar() * 1.2, sy = 0.5 + azar() * 0.8, sz = 0.8 + azar() * 1.0;
        casas.push({ color: colores[i % colores.length], x, z, sx, sy, sz, giro: azar() * 0.6 });
      }
    }
    const paredes = new THREE.InstancedMesh(geoCasa, new THREE.MeshStandardMaterial({ roughness: 0.9 }), casas.length);
    const techos = new THREE.InstancedMesh(geoTecho, matTeja, casas.length);
    casas.forEach((c, i) => {
      matriz.compose(posicion.set(c.x, 0, c.z), rotarY(c.giro), escala.set(c.sx, c.sy, c.sz));
      paredes.setMatrixAt(i, matriz);
      techos.setMatrixAt(i, matriz);
      paredes.setColorAt(i, color.setHex(c.color));
    });
    const copas = new THREE.InstancedMesh(geoCopa, matCopa, arboles.length);
    arboles.forEach((a, i) => {
      copas.setMatrixAt(i, matriz.compose(posicion.set(a.x, a.y, a.z), rotarY(0), escala.setScalar(a.s)));
      copas.setColorAt(i, color.setHex(a.color));
    });
    e.add(paredes, techos, copas);

    // cerro San Pedro con el Cristo de la Concordia y el teleférico
    this.cerro = new THREE.Group();
    const geoLoma = new THREE.SphereGeometry(7, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2);
    const pl = geoLoma.attributes.position;
    for (let i = 0; i < pl.count; i++) {
      if (pl.getY(i) < 0.01) continue;
      const k = 1 + (azar() - 0.5) * 0.08;
      pl.setXYZ(i, pl.getX(i) * k, pl.getY(i), pl.getZ(i) * k);
    }
    geoLoma.computeVertexNormals();
    const loma = new THREE.Mesh(geoLoma, new THREE.MeshStandardMaterial({ color: 0x9a8a57, flatShading: true, roughness: 1 }));
    loma.scale.set(1, 0.37, 0.75);
    this.cerro.add(loma);
    const arbustos = new THREE.InstancedMesh(geoCopa, matCopa, 14);
    for (let i = 0; i < 14; i++) {
      const a = azar() * Math.PI * 2;
      const r = 3 + azar() * 3.5;
      const y = 0.37 * Math.sqrt(Math.max(0, 49 - r * r));
      posicion.set(Math.cos(a) * r, y + 0.1, Math.sin(a) * r * 0.75);
      arbustos.setMatrixAt(i, matriz.compose(posicion, rotarY(0), escala.setScalar(0.5 + azar() * 0.3)));
      arbustos.setColorAt(i, color.setHex(coloresCopas[1 + (i % 2) * 2]));
    }
    this.cerro.add(arbustos);

    const cristo = crearCristoGLB(4);
    cristo.position.y = 2.5;
    cristo.rotation.y = -0.2;
    cristo.scale.setScalar(1.2);
    this.cerro.add(cristo);

    const tramo = (a, b, radio, mat) => {
      const dir = new THREE.Vector3().subVectors(b, a);
      const m = new THREE.Mesh(new THREE.CylinderGeometry(radio, radio, dir.length(), 6), mat);
      m.position.copy(a).add(b).multiplyScalar(0.5);
      m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
      return m;
    };
    const matCable = new THREE.MeshBasicMaterial({ color: 0x3a3a44 });
    const matEstacion = new THREE.MeshStandardMaterial({ color: 0xece6da, roughness: 0.8 });
    const matCabina = new THREE.MeshStandardMaterial({ color: 0xd8342f, roughness: 0.5 });
    const abajoEst = new THREE.Vector3(-8.5, 0.75, 5.5);
    const arribaEst = new THREE.Vector3(-1.9, 2.75, 1.2);
    this.cerro.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.7, 0.7), matEstacion), abajoEst.x, 0.35, abajoEst.z));
    this.cerro.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.6, 0.6), matEstacion), arribaEst.x, arribaEst.y - 0.4, arribaEst.z));
    for (const lado of [-0.12, 0.12]) {
      const desfase = new THREE.Vector3(0, 0, lado);
      this.cerro.add(tramo(abajoEst.clone().add(desfase), arribaEst.clone().add(desfase), 0.012, matCable));
    }
    for (const [f, subiendo] of [[0.22, 1], [0.48, -1], [0.74, 1]]) {
      const punto = abajoEst.clone().lerp(arribaEst, f);
      const cabina = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.24, 0.2), matCabina);
      cabina.position.set(punto.x, punto.y - 0.2, punto.z + subiendo * 0.12);
      this.cerro.add(cabina, tramo(punto.clone().setZ(punto.z + subiendo * 0.12), cabina.position, 0.008, matCable));
    }
    this.cerro.position.set(6, 0, -21);
    this.cerro.scale.setScalar(0.62);
    e.add(this.cerro);

    // edificio del Paseo Aranjuez
     this.paseo = crearEdificioGLB(7);
    this.paseo.position.set(-7, 0.5, -15);
    this.paseo.rotation.y = 0.4;
    this.paseo.scale.setScalar(1);
    e.add(this.paseo);
        // árboles de fondo (modelo GLB, se carga una vez y se clona)
    this.arboles = crearArboles('assets/modelos/arbol1.glb', [
      [-6.5, -7, 1.3],
      [6.5, -8, 1.5],
      [-10, -11, 1.4],
      [10, -12, 1.6],
      [-4.5, -13, 1.3],
      [4.5, -14, 1.5],
      [-11, -17, 1.7],
      [11, -18, 1.5],
      [-3.8, -20, 1.4],
      [3.8, -21, 1.6],
      [-13, -24, 1.8],
      [13, -25, 1.7],
      [-9, -29, 1.8],
      [8, -31, 1.9],
      [-16, -35, 2.0],
      [15, -37, 2.0],
      [-6, -41, 2.1],
      [7, -43, 2.2],
    ]);
    e.add(this.arboles);
      this.arbolGrande = crearArboles('assets/modelos/arbol1.glb', [
      [1.0, -6.5, 2.5],  
    ]);
    e.add(this.arbolGrande);
     this.arbolGrande.position.y = -0.3;
    this.lucesEdificio = [];
    const materialFocoEdificio = new THREE.MeshStandardMaterial({
      color: 0xffb347, emissive: 0xff8a2a, emissiveIntensity: 0.2, roughness: 0.3,
    });
    for (let i = 0; i < 7; i++) {
      const foco = new THREE.Mesh(new THREE.SphereGeometry(0.055, 12, 8), materialFocoEdificio);
      foco.position.set(-2.7 + i * 0.9, 0.18, 1.35);
      this.paseo.add(foco);
      this.lucesEdificio.push({ material: materialFocoEdificio });
    }
    for (const x of [-1.8, 0, 1.8]) {
      const luzEdificio = new THREE.PointLight(0xffa34d, 0, 3.8, 2);
      luzEdificio.position.set(x, 0.35, 1.1);
      this.paseo.add(luzEdificio);
      this.lucesEdificio.push({ luz: luzEdificio });
    }
    this.spotsTorre = [];
    for (const x of [-1.5, 2.1]) {
      const spot = new THREE.SpotLight(0xffa31a, 70, 18, 0.8, 0.6, 1);
      spot.position.set(x, 2.0, 3.0);              // antes y = 3.0; más abajo
      spot.target.position.set(x, 6.0, 0.0);       // antes 7.5; apunta más abajo
      this.paseo.add(spot);
      this.paseo.add(spot.target);
      this.spotsTorre.push(spot);
    }
    // this.paseo = new THREE.Group();
    // const vidrio = new THREE.MeshStandardMaterial({ color: 0x9cc7e0, metalness: 0.35, roughness: 0.2, emissive: 0x1d3a4f });
    // const losa = new THREE.MeshStandardMaterial({ color: 0xf2efe8, roughness: 0.7 });
    // this.paseo.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(5, 2.7, 2.6), vidrio), 0, 1.35, 0));
    // for (const y of [0.05, 0.9, 1.8, 2.7]) {
    //   this.paseo.add(colocar(new THREE.Mesh(new THREE.BoxGeometry(5.3, 0.12, 2.9), losa), 0, y, 0));
    // }
    // const letrero = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.6), new THREE.MeshBasicMaterial({ map: texturaLetrero() }));
    // letrero.position.set(0, 3.15, 1.0);
    // this.paseo.add(letrero);
    // this.paseo.position.set(-7, 0, -15);
    // this.paseo.rotation.y = 0.4;
    // this.paseo.scale.setScalar(0.75);
    // e.add(this.paseo);

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

    this.foquitos = [];
    this.lucesPlataforma = [];
    const materialFoco = new THREE.MeshStandardMaterial({
      color: 0xffc45c, emissive: 0xff8a2a, emissiveIntensity: 0.2, roughness: 0.35,
    });
    for (let i = 0; i < 8; i++) {
      const angulo = (i / 8) * Math.PI * 2;
      const foco = new THREE.Mesh(new THREE.SphereGeometry(0.035, 12, 8), materialFoco);
      foco.position.set(Math.cos(angulo) * 0.96, 0.08, Math.sin(angulo) * 0.96);
      this.foquitos.push(foco);
      e.add(foco);
    }
    for (const angulo of [0.2, Math.PI + 0.2, Math.PI / 2, Math.PI * 1.5]) {
      const luzFoco = new THREE.PointLight(0xffa34d, 0, 2.8, 2);
      luzFoco.position.set(Math.cos(angulo) * 0.82, 0.18, Math.sin(angulo) * 0.82);
      this.lucesPlataforma.push(luzFoco);
      e.add(luzFoco);
    }

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
    const pollera = this._pieza(geoPollera, this._toon(C.pollera, { side: THREE.DoubleSide }), 0.02);
    P.add(pollera);
    // La pollera se mece con resortes: se guardan los vértices en reposo para deformarlos en cada cuadro.
    p.setUsage(THREE.DynamicDrawUsage);
    const base = Float32Array.from(p.array);
    const angulos = new Float32Array(p.count);
    for (let i = 0; i < p.count; i++) angulos[i] = Math.atan2(base[i * 3 + 2], base[i * 3]) * 3;
    this.pollera = { malla: pollera, base, angulos, alto: 0.8, arriba: 0.85, franjas: [] };
    for (const [y, color] of [[0.16, 0x1f9d55], [0.22, 0xf2b705]]) {
      const radio = 0.44 - (y - 0.05) * 0.29;
      const franja = new THREE.Mesh(new THREE.CylinderGeometry(radio + 0.012, radio + 0.014, 0.03, 112, 1, true), this._toon(color, { side: THREE.DoubleSide }));
      franja.position.y = y;
      P.add(franja);
      this.pollera.franjas.push(franja);
    }

    // parte de arriba (respira)
    const T = (this.torso = new THREE.Group());
    P.add(T);
    const perfilTorso = [[0.2, 0.8], [0.215, 0.92], [0.205, 1.06], [0.18, 1.2], [0.13, 1.31], [0.07, 1.37]];
    T.add(this._pieza(new THREE.LatheGeometry(perfilTorso.map(([r, y]) => new THREE.Vector2(r, y)), 48), this._toon(C.blusa, { side: THREE.DoubleSide }), 0.02));

    // perfil de abajo hacia arriba: si no, las caras miran adentro y el contorno negro tapa la manta
    const perfilManta = [[0.295, 1.07], [0.293, 1.14], [0.282, 1.22], [0.245, 1.3], [0.16, 1.355], [0.075, 1.385]];
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
    for (const t of this.trenzas) T.add(t.grupo);

    this.cabeza = this._cabeza();
    T.add(this.cabeza);
  }

  /** Brazo: la manta cubre hasta el codo, luego la manga de la blusa con volado y la mano. */
  _brazo(s) {
    const largoBrazo = 0.28;
    const largoAntebrazo = 0.255;
    const hombro = new THREE.Group();
    hombro.position.set(s * 0.245, 1.255, 0.01);
    hombro.add(this._pieza(new THREE.CapsuleGeometry(0.054, 0.21, 6, 16).translate(0, -0.13, 0), this._toon(C.manta), 0.03));
    for (const [y, color] of [[-0.2, 0xf2b705], [-0.22, 0x1f9d55], [-0.238, 0x2b59c3]]) {
      const franja = new THREE.Mesh(new THREE.CylinderGeometry(0.0565, 0.0565, 0.016, 24, 1, true), this._toon(color, { side: THREE.DoubleSide }));
      franja.position.y = y;
      hombro.add(franja);
    }

    const codo = new THREE.Group();
    codo.position.y = -largoBrazo;
    codo.add(this._pieza(new THREE.CapsuleGeometry(0.04, 0.15, 6, 14).translate(0, -0.1, 0), this._toon(C.blusa), 0.03));
    const volado = new THREE.Mesh(new THREE.TorusGeometry(0.04, 0.014, 8, 24), this._toon(C.blusa));
    volado.rotation.x = Math.PI / 2;
    volado.position.y = -0.2;
    codo.add(volado);

    // mano: muñeca (gira sobre el antebrazo) > palma (se agita al saludar) > dedos con dos falanges y pulgar.
    // La palma mira a +z y los dedos cuelgan hacia −y; el pulgar queda del lado de afuera (s).
    const piel = this._toon(C.piel);
    const muneca = new THREE.Group();
    muneca.position.y = -largoAntebrazo + 0.012;
    const palma = new THREE.Group();
    muneca.add(palma);
    const dorso = this._pieza(new THREE.SphereGeometry(0.036, 18, 14), piel, 0.05);
    dorso.scale.set(0.98, 1.05, 0.56);
    dorso.position.y = -0.026;
    palma.add(dorso);
    const geoFalange = (radio, largo) => new THREE.CapsuleGeometry(radio, largo, 4, 8).translate(0, -largo / 2, 0);
    const dedos = [
      [0.021, 0.022, 0.018, 0.0078], [0.007, 0.025, 0.02, 0.008], [-0.007, 0.023, 0.018, 0.0076], [-0.02, 0.018, 0.015, 0.007],
    ].map(([x, largo1, largo2, radio]) => {
      const base = new THREE.Group();
      base.position.set(s * x, -0.056, 0.002);
      const proximal = this._pieza(geoFalange(radio, largo1), piel, 0.1, false);
      const nudillo = new THREE.Group();
      nudillo.position.y = -largo1;
      const distal = this._pieza(geoFalange(radio * 0.92, largo2), piel, 0.1, false);
      nudillo.add(distal);
      base.add(proximal, nudillo);
      palma.add(base);
      return { base, nudillo, curva: 0.4 };
    });
    const pulgar = new THREE.Group();
    pulgar.position.set(s * 0.03, -0.018, 0.012);
    const pulgarBase = this._pieza(geoFalange(0.009, 0.02), piel, 0.1, false);
    const pulgarNudillo = new THREE.Group();
    pulgarNudillo.position.y = -0.02;
    pulgarNudillo.add(this._pieza(geoFalange(0.0085, 0.016), piel, 0.1, false));
    pulgar.add(pulgarBase, pulgarNudillo);
    palma.add(pulgar);
    codo.add(muneca);
    hombro.add(codo);

    const pose = POSES_LADO.normal[s > 0 ? 1 : 0];
    const brazo = {
      s, hombro, codo, muneca, palma, dedos, largoBrazo, largoAntebrazo,
      pulgar: { base: pulgar, nudillo: pulgarNudillo, curva: 0.3 },
      abre: 0.05, giro: pose.giro,
      mano: pose.mano.clone(),
      polo: pose.codo.clone(),
    };
    this._resolverBrazo(brazo);
    this._ponerDedos(brazo, MANOS.relajada, 1, 0);
    return brazo;
  }

  /** Lleva los dedos hacia la forma `forma` (MANOS) con el factor k (0-1). */
  _ponerDedos(b, forma, k, t) {
    const s = b.s;
    b.abre += (forma.abre - b.abre) * k;
    b.dedos.forEach((d, i) => {
      d.curva += (forma.curva[i] + Math.sin(t * 0.7 + i) * 0.03 - d.curva) * k;
      d.base.rotation.set(-d.curva, 0, s * (1.5 - i) * b.abre * 0.9);
      d.nudillo.rotation.x = -d.curva * 1.15;
    });
    const p = b.pulgar;
    p.curva += (forma.pulgar - p.curva) * k;
    p.base.rotation.set(-0.35 - p.curva * 0.9, -s * p.curva * 0.6, s * (0.75 - p.curva * 0.55));
    p.nudillo.rotation.x = -p.curva * 0.8;
    b.muneca.rotation.y = b.giro;
  }

  /** IK de dos huesos: orienta hombro y codo para que la mano llegue a brazo.mano, con el codo hacia brazo.polo. */
  _resolverBrazo(b) {
    const S = b.hombro.position;
    const haciaMano = tmp.a.subVectors(b.mano, S);
    const d = THREE.MathUtils.clamp(haciaMano.length(), 0.05, b.largoBrazo + b.largoAntebrazo - 0.002);
    const dir = haciaMano.normalize();
    const cosA = (b.largoBrazo ** 2 + d ** 2 - b.largoAntebrazo ** 2) / (2 * b.largoBrazo * d);
    const angulo = Math.acos(THREE.MathUtils.clamp(cosA, -1, 1));
    const lado = tmp.b.copy(b.polo).addScaledVector(dir, -b.polo.dot(dir)).normalize();
    const codo = tmp.c.copy(S)
      .addScaledVector(dir, Math.cos(angulo) * b.largoBrazo)
      .addScaledVector(lado, Math.sin(angulo) * b.largoBrazo);
    b.hombro.quaternion.setFromUnitVectors(ABAJO, tmp.d.subVectors(codo, S).normalize());
    const antebrazo = tmp.d.copy(S).addScaledVector(dir, d).sub(codo).normalize()
      .applyQuaternion(tmp.q.copy(b.hombro.quaternion).invert());
    b.codo.quaternion.setFromUnitVectors(ABAJO, antebrazo);
  }

  _trenza(s) {
    const grupo = new THREE.Group();
    const curva = new THREE.CatmullRomCurve3([
      [0.12, 1.55, -0.06], [0.17, 1.45, 0.0], [0.22, 1.33, 0.14], [0.235, 1.2, 0.215], [0.225, 1.07, 0.245], [0.21, 0.95, 0.245],
    ].map(([x, y, z]) => new THREE.Vector3(s * x, y, z)));
    const geo = new THREE.SphereGeometry(1, 12, 8);
    const arriba = new THREE.Vector3(0, 1, 0);
    const n = 20;
    const nudos = new THREE.InstancedMesh(geo, this._toon(C.cabello), n + 1);
    nudos.castShadow = true;
    nudos.frustumCulled = false;
    const raiz = curva.getPoint(0);
    const base = [];
    for (let i = 0; i <= n; i++) {
      const t = i / n;
      const punto = curva.getPoint(t);
      const tangente = curva.getTangent(t);
      const lado = new THREE.Vector3().crossVectors(tangente, new THREE.Vector3(0, 0, 1)).normalize();
      const radio = 0.03 * (1 - 0.35 * t);
      base.push({
        pos: punto.addScaledVector(lado, (i % 2 ? 1 : -1) * 0.008).sub(raiz),
        giro: new THREE.Quaternion().setFromUnitVectors(arriba, tangente),
        escala: new THREE.Vector3(radio, radio * 1.7, radio * 0.85),
        peso: t ** 1.3,
      });
    }
    grupo.add(nudos);
    const fin = curva.getPoint(1);
    const punta = new THREE.Group();
    const cordon = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.05, 6), this._toon(0xd62f5b));
    cordon.position.set(0, -0.035, 0);
    punta.add(cordon);
    for (const [dx, dy, color] of [[0, -0.07, 0xd62f5b], [-0.018, -0.1, 0xf2b705], [0.018, -0.1, 0x1f9d55]]) {
      const pompon = this._pieza(new THREE.SphereGeometry(0.022, 14, 10), this._toon(color), 0.06);
      pompon.position.set(dx, dy, 0.01);
      punta.add(pompon);
    }
    grupo.add(punta);
    const trenza = {
      s, grupo, nudos, base, raiz, punta, fin: fin.sub(raiz),
      ladeo: { x: 0, v: 0 }, vaiven: { x: 0, v: 0 }, rot: new THREE.Quaternion(), euler: new THREE.Euler(),
    };
    this._doblarTrenza(trenza);
    return trenza;
  }

  /** Dobla la trenza desde la raíz: cada nudo gira según cuánto cuelga (peso), la punta gira entera. */
  _doblarTrenza(tr) {
    const { a, q, m } = tmp;
    tr.base.forEach((b, i) => {
      tr.euler.set(tr.vaiven.x * b.peso, 0, tr.ladeo.x * b.peso);
      tr.rot.setFromEuler(tr.euler);
      a.copy(b.pos).applyQuaternion(tr.rot).add(tr.raiz);
      q.copy(tr.rot).multiply(b.giro);
      tr.nudos.setMatrixAt(i, m.compose(a, q, b.escala));
    });
    tr.nudos.instanceMatrix.needsUpdate = true;
    tr.euler.set(tr.vaiven.x, 0, tr.ladeo.x);
    tr.punta.quaternion.setFromEuler(tr.euler);
    tr.punta.position.copy(tr.fin).applyQuaternion(tr.punta.quaternion).add(tr.raiz);
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

    // ojos: dentro de `envoltura` (achatada) el globo es una esfera, así el iris gira sobre ella al mirar y
    // los párpados (casquetes apenas más grandes) lo tapan por completo al parpadear
    ref.iris = [];
    ref.parpadosSup = [];
    ref.parpadosInf = [];
    const R = 0.026;
    // anillos finos (no un abanico de triángulos grandes) para que el iris siga la curva del globo sin hundirse
    const geoIris = new THREE.RingGeometry(0.00005, 0.0142, 32, 8);
    const pi = geoIris.attributes.position;
    for (let i = 0; i < pi.count; i++) {
      const x = pi.getX(i), y = pi.getY(i) / 0.78;
      pi.setXYZ(i, x, y, Math.sqrt(Math.max(0, (R + 0.0004) ** 2 - x * x - y * y)));
    }
    const matIris = new THREE.MeshBasicMaterial({ map: texturaIris() });
    const matBrillo = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const matPestana = new THREE.MeshBasicMaterial({ color: 0x140c0a });
    const matParpado = this._toon(C.piel);
    const sobreGlobo = (malla, x, y, radio) => {
      const z = Math.sqrt(radio * radio - x * x - y * y);
      malla.position.set(x, y, z);
      malla.lookAt(x * 2, y * 2, z * 2);
      return malla;
    };
    for (const s of [-1, 1]) {
      const ojo = new THREE.Group();
      ojo.position.set(s * 0.052, centro.y + 0.012, superficie(0.052, 0.012) - 0.008);
      const envoltura = new THREE.Group();
      envoltura.scale.set(1, 0.78, 0.5);
      const blanco = new THREE.Mesh(new THREE.SphereGeometry(R, 24, 16), this._toon(0xfffaf3));
      const iris = new THREE.Group();
      iris.add(new THREE.Mesh(geoIris, matIris));
      iris.add(sobreGlobo(new THREE.Mesh(new THREE.CircleGeometry(0.0036, 12), matBrillo), 0.0048, 0.0085, R + 0.0006));
      iris.add(sobreGlobo(new THREE.Mesh(new THREE.CircleGeometry(0.0017, 10), matBrillo), -0.0052, -0.0052, R + 0.0006));
      const sup = new THREE.Group();
      sup.add(new THREE.Mesh(new THREE.SphereGeometry(R * 1.06, 24, 10, 0, Math.PI * 2, 0, Math.PI / 2), matParpado));
      const pestanas = new THREE.Mesh(new THREE.TorusGeometry(R * 1.06, 0.0034, 6, 24, Math.PI), matPestana);
      pestanas.rotation.x = Math.PI / 2;
      pestanas.scale.set(1, 1, 1.5);
      const rabillo = new THREE.Mesh(new THREE.ConeGeometry(0.0034, 0.011, 6), matPestana);
      rabillo.position.set(s * R * 1.08, 0.0035, 0.004);
      rabillo.rotation.z = -s * 1.0;
      sup.add(pestanas, rabillo);
      const inf = new THREE.Group();
      inf.add(new THREE.Mesh(new THREE.SphereGeometry(R * 1.05, 24, 8, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), matParpado));
      const borde = new THREE.Mesh(new THREE.TorusGeometry(R * 1.05, 0.0012, 4, 24, Math.PI), new THREE.MeshBasicMaterial({ color: 0x8a5a3e }));
      borde.rotation.x = Math.PI / 2;
      inf.add(borde);
      envoltura.add(blanco, iris, sup, inf);
      ojo.add(envoltura);
      pivote.add(ojo);
      ref.iris.push(iris);
      ref.parpadosSup.push(sup);
      ref.parpadosInf.push(inf);
    }

    // cejas: gruesas hacia la nariz, finas hacia afuera y arqueadas sobre la curva de la frente
    ref.cejas = [-1, 1].map((s) => {
      const geo = new THREE.CapsuleGeometry(0.0046, 0.034, 4, 10).rotateZ(Math.PI / 2);
      const pc = geo.attributes.position;
      for (let i = 0; i < pc.count; i++) {
        const x = pc.getX(i), y = pc.getY(i), z = pc.getZ(i);
        const u = limitar(x / 0.021, -1, 1);
        const adentro = (1 - s * u) / 2;
        const grosor = 0.45 + 0.7 * adentro;
        const arco = 0.0055 * (1 - ((u * s - 0.15) / 1.15) ** 2);
        pc.setXYZ(i, x, y * grosor + arco, z * grosor - (x * x) / (2 * 0.14));
      }
      geo.computeVertexNormals();
      const ceja = new THREE.Mesh(geo, oscuro);
      ceja.rotation.z = s * 0.06;
      ceja.position.set(s * 0.055, centro.y + 0.058, superficie(0.055, 0.058) + 0.001);
      ceja.userData = { y: ceja.position.y, giro: ceja.rotation.z, s };
      pivote.add(ceja);
      return ceja;
    });

    const nariz = new THREE.Mesh(new THREE.SphereGeometry(0.016, 16, 12), this._toon(C.pielOscura));
    nariz.scale.set(0.9, 1.2, 1);
    nariz.position.set(0, centro.y - 0.028, superficie(0, -0.028) + 0.002);
    pivote.add(nariz);

    ref.mejillas = [-1, 1].map((s) => {
      const normal = new THREE.Vector3(s * 0.085, -0.04 / 1.25, superficie(0.085, -0.04)).normalize();
      const mejilla = new THREE.Mesh(new THREE.CircleGeometry(0.026, 24), new THREE.MeshBasicMaterial({ color: 0xe0676a, transparent: true, opacity: 0.35, depthWrite: false }));
      mejilla.position.set(s * 0.085, centro.y - 0.04, superficie(0.085, -0.04) + 0.003);
      mejilla.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
      mejilla.userData.y = mejilla.position.y;
      pivote.add(mejilla);
      return mejilla;
    });

    // boca: labios, interior, dientes y lengua que toman la forma de cada sonido
    const lados = { side: THREE.DoubleSide };
    ref.boca = new BocaFlexible({
      interior: new THREE.MeshBasicMaterial({ color: C.boca, ...lados }),
      lengua: new THREE.MeshBasicMaterial({ color: C.lengua, ...lados }),
      dientes: new THREE.MeshBasicMaterial({ color: 0xfbf7f0, ...lados }),
      labioSup: this._toon(C.labioSup, lados),
      labioInf: this._toon(C.labio, lados),
    });
    const boca = ref.boca.grupo;
    boca.position.set(0, centro.y - 0.075, superficie(0, -0.075));
    boca.rotation.x = 0.42;
    ref.boca.actualizar(FORMAS.reposo, this.sonrisa);
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
    this.compositor?.setSize(w, h);
    const cam = this.camara;
    cam.aspect = w / h;
    const tanV = Math.tan(THREE.MathUtils.degToRad(cam.fov / 2));
    const { arriba, abajo, izquierda, derecha } = this.margenes;
    const altoLibre = Math.max(0.3, (h - arriba - abajo) / h);
    const anchoLibre = Math.max(0.3, (w - izquierda - derecha) / w);
    // de la mitad de la pollera (y≈0.45) a la copa del sombrero (y≈2.07), con el brazo en alto para saludar
    this.distancia = Math.max(0.86 / (tanV * altoLibre), 0.52 / (tanV * cam.aspect * anchoLibre));
    // medio ancho visible (sin los paneles) a esa profundidad: el Cristo y el Paseo quedan a la vista, no detrás de la interfaz
    const libre = (objeto) => tanV * cam.aspect * anchoLibre * (this.distancia - objeto.position.z);
    this.cerro.position.x = Math.min(12, libre(this.cerro) * 0.78);
    this.paseo.position.x = -Math.min(9, libre(this.paseo) * 0.7);
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

  _actualizarHoraDelDia() {
    const ahora = new Date();
    //const hora=2;
    const hora = ahora.getHours() + ahora.getMinutes() / 60;
    if (Math.abs(hora - this.ultimaHoraDia) < 1 / 120) return;
    this.ultimaHoraDia = hora;

    const dia = limitar(Math.sin(((hora - 6) / 12) * Math.PI), 0, 1);
    const amanecer = limitar(1 - Math.abs(hora - 7) / 1.8, 0, 1);
    const atardecer = limitar(1 - Math.abs(hora - 18) / 2.2, 0, 1);
    const dorado = Math.max(amanecer, atardecer);

    this.luzCielo.intensity = 0.55 + dia * 0.9;
    this.luzCielo.color.setRGB(0.58 + dia * 0.24, 0.68 + dia * 0.22, 0.98);
    this.luzCielo.groundColor.setRGB(0.12 + dia * 0.3, 0.1 + dia * 0.2, 0.18 + dia * 0.12);

    this.luzPrincipal.intensity = 0.55 + dia * 2.05 + dorado * 0.3;
    this.luzPrincipal.color.setRGB(1, 0.72 + dia * 0.2, 0.5 + dia * 0.35);
    this.luzRelleno.intensity = 0.35 + dia * 0.55;
    this.luzRelleno.color.setRGB(0.35 + dia * 0.25, 0.55 + dia * 0.25, 1);
    this.luzContraluz.intensity = 0.35 + dorado * 1.1;
    this.luzContraluz.color.setRGB(1, 0.34 + dia * 0.35, 0.18 + dia * 0.25);

    this.sol.material.opacity = 0.08 + dia * 0.92 + dorado * 0.12;
    this.sol.material.color.setRGB(1, 0.55 + dia * 0.35, 0.25 + dia * 0.55);
    this.sol.position.x = Math.cos(((hora - 12) / 12) * Math.PI) * 38;
    this.sol.position.y = 8 + dia * 24;
    this.sol.position.z = -52 - dia * 18;

    for (const [nombre, colores] of Object.entries(CIELO)) {
      this.materialCielo.uniforms[`c${nombre[0].toUpperCase()}${nombre.slice(1)}`].value
        .copy(colores.noche)
        .lerp(colores.dia, dia)
        .lerp(colores.dorado, dorado * 0.7);
    }

    const noche = 1 - dia;
    for (const luz of this.lucesPlataforma) luz.intensity = noche * 0.75;
    for (const foco of this.foquitos) foco.material.emissiveIntensity = 0.2 + noche * 2.2;
    for (const elemento of this.lucesEdificio) {
      if (elemento.luz) elemento.luz.intensity = noche * 1.1;
      if (elemento.material) elemento.material.opacity = 0.08 + noche * 0.92;
    }
  }

  /** Movimientos de reposo variados para que no se vea en bucle; nunca repite el anterior. */
  _accionReposo(ahora) {
    const acciones = ["mirar", "mirar", "peso", "ladear", "sonreir", "parpadeo", "suspiro", "trenza", "sombrero"]
      .filter((a) => a !== this.ultimaAccion);
    const accion = acciones[Math.floor(Math.random() * acciones.length)];
    this.ultimaAccion = accion;
    switch (accion) {
      case "mirar":
        this.puntoMirada.set((Math.random() - 0.5) * 1.4, (Math.random() - 0.3) * 0.6);
        this.mirarHasta = ahora + 1200 + Math.random() * 1000;
        break;
      case "peso": this.pesoObjetivo = this.pesoObjetivo ? 0 : (Math.random() < 0.5 ? -1 : 1) * 0.012; break;
      case "ladear":
        this.inclinacionExtra = (Math.random() < 0.5 ? -1 : 1) * 0.07;
        this.inclinarHasta = ahora + 2200;
        break;
      case "sonreir": this.sonreir(0.8, 2200); break;
      case "parpadeo": this.parpadeo = ahora; this.proximoParpadeo = ahora + 230; break;
      case "suspiro": this.suspiroDesde = ahora; break;
      case "trenza": this.gesto("trenza", 2200); break;
      case "sombrero": this.gesto("sombrero", 1700); break;
    }
  }

  _cuadro() {
    const real = this.reloj.getDelta();
    const dt = Math.min(real, 0.05);
    const t = this.reloj.elapsedTime;
    const ahora = performance.now();
    const suave = (k) => 1 - Math.exp(-dt * k);
    const r = this.rostro;
    const estado = this._estado;
    const hablando = !!(this.analizador || this.simulado);
    this._actualizarHoraDelDia();

    // boca: forma del sonido que suena (plan alineado al audio), de la palabra (voz del navegador) o del volumen
    const objetivo = this._forma;
    if (this.analizador) {
      const volumen = this._volumen();
      const tAudio = this.audio?.currentTime ?? 0;
      if (this.plan) {
        formaEn(this.plan, tAudio, objetivo);
        const k = palabraEn(this.plan, tAudio);
        if (this.alProgresar && k >= 0 && k !== this.ultimaPalabra) {
          this.ultimaPalabra = k;
          this.alProgresar(Math.min(0.99, (k + 0.5) / this.plan.palabras.length));
        }
      } else {
        formaPorVolumen(volumen, t, objetivo);
        if (this.alProgresar && this.audio?.duration) this.alProgresar(tAudio / this.audio.duration);
      }
    } else if (this.simulado && this.palabraSim) {
      formaEn(this.palabraSim.plan, (ahora - this.palabraSim.desde) / 1000, objetivo);
    } else if (this.simulado) {
      formaPorVolumen(0.015 + (0.2 + 0.6 * Math.abs(Math.sin(t * 12.7) * Math.sin(t * 5.3))) / 7, t, objetivo);
    } else {
      Object.assign(objetivo, FORMAS.reposo);
    }
    // la boca usa el tiempo real (no el limitado) para no atrasarse respecto del audio en equipos lentos
    const dtBoca = Math.min(real, 0.12);
    for (const k of CLAVES_BOCA) {
      this.boca[k] += (objetivo[k] - this.boca[k]) * (1 - Math.exp(-dtBoca * (objetivo[k] > this.boca[k] ? 30 : 20)));
    }
    const habla = Math.min(1, this.boca.abre * 2);
    const sonrisaObjetivo = ahora < this.finSonrisa ? this.intensidadSonrisa
      : estado === "pensando" ? 0.1 : estado === "escuchando" ? 0.4 : hablando ? 0.25 : 0.3;
    this.sonrisa += (sonrisaObjetivo - this.sonrisa) * suave(4);
    r.boca.actualizar(this.boca, this.sonrisa);

    // reposo: pequeñas acciones al azar cuando no está haciendo nada
    if (ahora > this.proximoReposo) {
      this.proximoReposo = ahora + 4000 + Math.random() * 5000;
      if (estado === "normal" && !hablando && this.gestoActual === "normal") this._accionReposo(ahora);
    }

    // hacia dónde mira: un punto pedido (tarjetas, reposo), al usuario si escucha, el puntero o deambula
    const destino = tmp.v2;
    if (ahora < this.mirarHasta) destino.copy(this.puntoMirada);
    else if (estado === "escuchando") destino.set(0, 0.1);
    else if (ahora - this.ultimoPuntero < 4000) destino.copy(this.puntero);
    else destino.set(Math.sin(t * 0.23) * 0.4, Math.sin(t * 0.31) * 0.2);
    this.mirada.lerp(destino, suave(ahora < this.mirarHasta ? 7 : 4));

    // cabeza
    if (ahora > this.inclinarHasta) this.inclinacionExtra += (0 - this.inclinacionExtra) * suave(2);
    let giro = this.mirada.x * 0.35;
    let cabeceo = -this.mirada.y * 0.15;
    let inclinacion = Math.sin(t * 0.5) * 0.03 + this.inclinacionExtra;
    if (estado === "pensando") { giro = 0.14; cabeceo = -0.13; inclinacion = 0.1; }
    if (estado === "escuchando") { inclinacion = 0.09; cabeceo = 0.04; }
    const sorprendida = ahora < this.sorpresaHasta;
    if (sorprendida) cabeceo -= 0.06;
    giro += Math.sin(t * 1.7) * 0.05 * habla;
    cabeceo += Math.sin(t * 3.1) * 0.035 * habla;
    inclinacion += Math.sin(t * 2.3) * 0.025 * habla;
    const base = this.cabezaBase;
    base.y += (giro - base.y) * suave(5);
    base.x += (cabeceo - base.x) * suave(sorprendida ? 12 : 5);
    base.z += (inclinacion - base.z) * suave(4);
    const d = (ahora - this.asentirDesde) / 1000;
    const asiente = d < 0.8 ? 0.08 * Math.sin((Math.PI * d) / 0.4) ** 2 * (1 - d) : 0;
    const cab = this.cabeza.rotation;
    cab.set(base.x + asiente, base.y, base.z);

    // ojos: iris hacia la mirada (arriba al pensar), parpadeo, ojos felices al sonreír, abiertos al sorprenderse
    const irisY = estado === "pensando" ? 0.2 : this.mirada.x * 0.23;
    const irisX = estado === "pensando" ? -0.32 : -this.mirada.y * 0.16;
    for (const iris of r.iris) {
      iris.rotation.y += (irisY - iris.rotation.y) * suave(14);
      iris.rotation.x += (irisX - iris.rotation.x) * suave(14);
    }
    if (ahora > this.proximoParpadeo) { this.parpadeo = ahora; this.proximoParpadeo = ahora + 2200 + Math.random() * 3500; }
    const fase = (ahora - this.parpadeo) / 70;
    const cierre = fase >= 0 && fase < 2 ? 1 - Math.abs(1 - fase) : 0;
    const feliz = Math.max(0, this.sonrisa - 0.45) / 0.55;
    const abierto = sorprendida ? -1.25 : estado === "pensando" ? -1.15 : -1.02 - this.mirada.y * 0.12 + feliz * 0.15;
    this.parpado.sup += (abierto - this.parpado.sup) * suave(12);
    this.parpado.inf += (0.95 - feliz * 0.45 - this.parpado.inf) * suave(8);
    const sup = this.parpado.sup + (1.25 - this.parpado.sup) * cierre;
    for (const p of r.parpadosSup) p.rotation.x = sup;
    for (const p of r.parpadosInf) p.rotation.x = this.parpado.inf;

    // cejas: suben al escuchar y al sorprenderse, una se arquea al pensar, acompañan el énfasis al hablar
    const subir = sorprendida ? 1 : estado === "escuchando" ? 0.7 : estado === "pensando" ? 0.35 : habla * 0.45 + feliz * 0.25;
    const interior = estado === "escuchando" ? 0.5 : sorprendida ? 0.3 : 0;
    r.cejas.forEach((ceja, i) => {
      const extra = estado === "pensando" && i === 1 ? 0.7 : 0;
      this.cejas.subir[i] += (subir + extra - this.cejas.subir[i]) * suave(9);
      this.cejas.interior[i] += (interior - this.cejas.interior[i]) * suave(6);
      const { y, giro: giroBase, s } = ceja.userData;
      ceja.position.y = y + this.cejas.subir[i] * 0.008;
      ceja.rotation.z = giroBase - s * this.cejas.interior[i] * 0.22 + s * (estado === "pensando" && i === 0 ? 0.08 : 0);
    });
    for (const mejilla of r.mejillas) {
      mejilla.position.y = mejilla.userData.y + this.sonrisa * 0.004;
      mejilla.material.opacity = 0.28 + this.sonrisa * 0.17;
    }

    // cuerpo: respiración (con algún suspiro), cambio de peso, se inclina hacia el usuario al escucharlo
    const ds = (ahora - this.suspiroDesde) / 1800;
    const suspiro = ds >= 0 && ds < 1 ? Math.sin(Math.PI * ds) : 0;
    const respira = Math.sin(t * 1.7);
    this.cadera += (this.pesoObjetivo - this.cadera) * suave(1.6);
    this.torso.position.set(this.cadera, respira * 0.004 + suspiro * 0.007, 0);
    this.manta.scale.set(1 + respira * 0.006 + suspiro * 0.012, 1, 1 + respira * 0.006 + suspiro * 0.012);
    this.personaje.rotation.y += (cab.y * 0.25 - this.personaje.rotation.y) * suave(2);
    const inclinarTorso = estado === "escuchando" ? 0.06 : estado === "pensando" ? -0.015 : 0;
    this.torso.rotation.x += (inclinarTorso - this.torso.rotation.x) * suave(3);
    this.torso.rotation.z = -this.cadera * 1.2;
    this._animarTelas(dt, t, cab);

    // aretes como péndulos que reaccionan al giro de la cabeza
    const a = this.aretes;
    const velGiro = (cab.y - a.giroPrevio) / Math.max(dt, 1e-3);
    a.giroPrevio = cab.y;
    a.velocidad += (-60 * a.angulo - 4 * a.velocidad - velGiro * 6) * dt;
    a.angulo += a.velocidad * dt;
    for (const arete of r.aretes) arete.rotation.set(a.angulo * 0.5, 0, a.angulo + Math.sin(t * 2) * 0.05);

    // brazos hacia la pose del gesto, con la forma de mano y el giro de muñeca de esa pose
    if (this.finGesto && ahora > this.finGesto) { this.gestoActual = "normal"; this.finGesto = 0; }
    for (const b of this.brazos) {
      const lado = b.s > 0 ? 1 : 0;
      const señala = this.gestoActual === "señalar" && b.s === this.señal.s;
      const pose = POSES_LADO[señala || this.gestoActual === "señalar" ? "normal" : this.gestoActual][lado];
      const destinoMano = señala ? this.señal.mano : pose.mano;
      const polo = señala ? tmp.polo.set(b.s, -0.6, -0.35) : pose.codo;
      const ola = señala ? 0 : pose.ola;
      tmp.mano.copy(destinoMano);
      if (ola) tmp.mano.x += Math.sin(t * ola) * 0.06;
      tmp.mano.y += respira * 0.004;
      b.mano.lerp(tmp.mano, suave(ola ? 10 : 6));
      b.polo.lerp(polo, suave(6));
      this._resolverBrazo(b);
      b.giro += ((señala ? -b.s * 1.5 : pose.giro) - b.giro) * suave(8);
      b.palma.rotation.z = ola ? Math.sin(t * ola) * 0.3 : 0;
      this._ponerDedos(b, MANOS[señala ? "señalar" : pose.dedos], suave(10), t);
    }

    // plataforma: color del estado, pulso con la voz
    const color = tmp.color.setHex(COLOR_ESTADO[estado]);
    this.halo.material.color.lerp(color, suave(4));
    this.anillo.material.color.lerp(color, suave(4));
    this.halo.material.opacity = 0.35 + Math.sin(t * 2.2) * 0.1 + this.boca.abre * 0.35;
    this.halo.scale.setScalar(1 + this.boca.abre * 0.08 + (estado === "escuchando" ? Math.sin(t * 6) * 0.04 : 0));

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

    cam.layers.set(0);
    this.compositor.render();
    this.renderer.autoClear = false;
    this.renderer.clearDepth();
    cam.layers.set(1);
    this.renderer.render(this.escena, cam);
    cam.layers.enable(0);
    this.renderer.autoClear = true;
    this._ajustarCalidad(real, ahora);
  }

  /** Pollera y trenzas con resortes: se quedan atrás al girar o mover la cadera y se mecen un poco al hablar. */
  _animarTelas(dt, t, cab) {
    const f = this.fisica;
    const cuerpo = this.personaje.rotation.y;
    const dGiro = cuerpo - f.giroPrevio;
    const dCadera = this.cadera - f.caderaPrevia;
    const dCabeza = cab.y - f.cabezaPrevia;
    f.giroPrevio = cuerpo;
    f.caderaPrevia = this.cadera;
    f.cabezaPrevia = cab.y;

    f.polleraGiro.x -= dGiro * 0.8;
    resorte(f.polleraGiro, 0, dt, 38, 4.5);
    f.polleraX.x -= dCadera * 0.9;
    resorte(f.polleraX, Math.sin(t * 0.9) * 0.002, dt, 30, 4);
    resorte(f.polleraZ, -this.torso.rotation.x * 0.05, dt, 30, 4);

    const P = this.pollera;
    const pos = P.malla.geometry.attributes.position;
    const arr = pos.array, b = P.base;
    const mueve = Math.min(1, Math.abs(f.polleraGiro.v) * 3 + Math.abs(f.polleraX.v) * 40);
    for (let i = 0, j = 0; i < arr.length; i += 3, j++) {
      const x = b[i], y = b[i + 1], z = b[i + 2];
      const caida = limitar((P.alto / 2 - y) / P.alto, 0, 1);
      const c2 = caida * caida;
      const ang = f.polleraGiro.x * c2;
      const cos = Math.cos(ang), sin = Math.sin(ang);
      const onda = 1 + Math.sin(P.angulos[j] + t * 2.4) * 0.012 * caida * (0.25 + mueve);
      arr[i] = (x * cos - z * sin) * onda + this.cadera * (1 - caida) + f.polleraX.x * c2;
      arr[i + 1] = y;
      arr[i + 2] = (x * sin + z * cos) * onda + f.polleraZ.x * c2;
    }
    pos.needsUpdate = true;
    for (const franja of P.franjas) {
      const caida = limitar((P.arriba - franja.position.y) / P.alto, 0, 1);
      franja.rotation.y = f.polleraGiro.x * caida * caida;
      franja.position.x = this.cadera * (1 - caida) + f.polleraX.x * caida * caida;
      franja.position.z = f.polleraZ.x * caida * caida;
    }

    for (const tr of this.trenzas) {
      tr.ladeo.v -= dCabeza * 1.5 + dGiro * 2 + dCadera * 6;
      resorte(tr.ladeo, Math.sin(t * 1.3 + tr.s) * 0.012 - cab.y * 0.03 - this.torso.rotation.z, dt, 26, 3.5);
      resorte(tr.vaiven, -this.torso.rotation.x - cab.x * 0.15, dt, 26, 3.5);
      tr.ladeo.x = limitar(tr.ladeo.x, -0.05, 0.05);
      tr.vaiven.x = limitar(tr.vaiven.x, -0.09, 0.015);
      this._doblarTrenza(tr);
    }
  }

  /** Baja la resolución interna si el equipo no llega a ~40 cuadros por segundo y la recupera si sobra. */
  _ajustarCalidad(real, ahora) {
    const c = this.calidad;
    if (!c.activa || real > 1) return;
    c.suma += real;
    c.cuadros++;
    if (c.suma < 2) return;
    const promedio = c.suma / c.cuadros;
    c.suma = c.cuadros = 0;
    const actual = this.renderer.getPixelRatio();
    let nuevo = actual;
    if (promedio > 1 / 40 && actual > c.minima) nuevo = Math.max(c.minima, actual * 0.85);
    else if (promedio < 1 / 57 && actual < c.maxima && ahora - c.ultimoCambio > 8000) nuevo = Math.min(c.maxima, actual + 0.1);
    if (nuevo !== actual) {
      c.ultimoCambio = ahora;
      this.renderer.setPixelRatio(nuevo);
      this._redimensionar();
    }
  }
}
