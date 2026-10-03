// Habla de Paseito: convierte una frase en formas de boca (visemas) y las alinea con su audio.
// El español se pronuncia casi como se escribe, así que bastan reglas de letras. El TTS no entrega
// marcas de tiempo por palabra: la alineación se estima con las pausas reales del audio (silencios)
// frente a la puntuación y los espacios del texto, y la energía de la voz modula la apertura.
// No depende de Three.js: lo usan el avatar 3D y el 2D.

export const PASO = 0.01; // s por cuadro de análisis

/** abre: mandíbula/labios (0-1) · ancho: comisuras (1 = neutro) · redondo: labios en "o" · presion: labios apretados · dientes: cuánto se ven */
export const FORMAS = {
  reposo: { abre: 0, ancho: 1, redondo: 0, presion: 0, dientes: 0 },
  A: { abre: 1, ancho: 1.06, redondo: 0, presion: 0, dientes: 0.6 },
  E: { abre: 0.55, ancho: 1.2, redondo: 0, presion: 0, dientes: 0.85 },
  I: { abre: 0.3, ancho: 1.3, redondo: 0, presion: 0, dientes: 1 },
  O: { abre: 0.68, ancho: 0.78, redondo: 0.8, presion: 0, dientes: 0.2 },
  U: { abre: 0.3, ancho: 0.64, redondo: 1, presion: 0, dientes: 0 },
  MBP: { abre: 0, ancho: 0.96, redondo: 0, presion: 1, dientes: 0 },
  FV: { abre: 0.1, ancho: 1.04, redondo: 0, presion: 0.35, dientes: 1 },
  L: { abre: 0.3, ancho: 1.02, redondo: 0, presion: 0, dientes: 0.7 },
  S: { abre: 0.14, ancho: 1.16, redondo: 0, presion: 0, dientes: 1 },
  K: { abre: 0.4, ancho: 0.96, redondo: 0, presion: 0, dientes: 0.5 },
  CH: { abre: 0.2, ancho: 0.8, redondo: 0.55, presion: 0, dientes: 0.8 },
};
const CLAVES = Object.keys(FORMAS.reposo);
// duración relativa de cada sonido; R es la "r" simple y RR la vibrante
const PESOS = { A: 1, E: 1, I: 0.9, O: 1, U: 0.9, MBP: 0.75, FV: 0.8, L: 0.6, R: 0.42, RR: 0.85, S: 0.85, K: 0.7, CH: 0.85 };
const FORMA_DE = { R: "L", RR: "L" };
const TILDES = { á: "a", é: "e", í: "i", ó: "o", ú: "u" };
const ABREVIATURAS = { bs: "bolivianos", av: "avenida", nro: "número", dr: "doctor", dra: "doctora", sr: "señor", sra: "señora", km: "kilómetros" };

const UNIDADES = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce",
  "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós",
  "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"];
const DECENAS = ["", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"];
const CENTENAS = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"];

function menorQueMil(n) {
  if (n === 100) return "cien";
  const resto = n % 100;
  const partes = [CENTENAS[Math.floor(n / 100)]];
  if (resto) partes.push(resto < 30 ? UNIDADES[resto] : DECENAS[Math.floor(resto / 10)] + (resto % 10 ? " y " + UNIDADES[resto % 10] : ""));
  return partes.filter(Boolean).join(" ");
}

function numero(n) {
  if (!Number.isFinite(n)) return "";
  if (n < 30) return UNIDADES[n];
  if (n < 1000) return menorQueMil(n);
  if (n < 1e6) {
    const miles = Math.floor(n / 1000), resto = n % 1000;
    return (miles === 1 ? "mil" : menorQueMil(miles) + " mil") + (resto ? " " + menorQueMil(resto) : "");
  }
  return String(n).split("").map((d) => UNIDADES[+d]).join(" ");
}

/** Lo que el TTS realmente pronuncia: números, horas y abreviaturas escritos con letras. */
function expandir(palabra) {
  let t = palabra.toLowerCase().replace(/[¿¡"«»“”()[\]{}…!?;,]/g, " ").trim();
  const abreviatura = ABREVIATURAS[t.replace(/\.$/, "")];
  if (abreviatura) return abreviatura;
  t = t.replace(/(\d{1,2}):(\d{2})/g, (_, h, m) => numero(+h) + (+m ? " " + numero(+m) : ""));
  t = t.replace(/\d+(?:[.,]\d+)?/g, (n) => {
    const [entero, decimal] = n.split(/[.,]/);
    return numero(+entero) + (decimal ? " coma " + numero(+decimal) : "");
  });
  return t.replace(/[.:\-–—/]/g, " ");
}

/** Sonidos de una palabra escrita: [[forma, peso], ...]. */
export function fonemas(palabra) {
  const salida = [];
  for (const p of expandir(palabra).split(/\s+/)) {
    for (let i = 0; i < p.length; i++) {
      const original = p[i];
      const tonica = original in TILDES;
      const c = TILDES[original] || original;
      const sig = TILDES[p[i + 1]] || p[i + 1] || "";
      const ant = TILDES[p[i - 1]] || p[i - 1] || "";
      const agregar = (v) => {
        const forma = FORMA_DE[v] || v;
        const peso = PESOS[v] * (tonica ? 1.3 : 1);
        const ultimo = salida[salida.length - 1];
        if (ultimo && ultimo[0] === forma && forma !== "A" && forma !== "E" && forma !== "O") ultimo[1] += peso * 0.5;
        else salida.push([forma, peso]);
      };
      switch (c) {
        case "a": case "e": case "i": case "o": agregar(c.toUpperCase()); break;
        case "u": if (!((ant === "q" || ant === "g") && (sig === "e" || sig === "i"))) agregar("U"); break;
        case "ü": agregar("U"); break;
        case "y": agregar(i === p.length - 1 || !"aeiou".includes(sig) ? "I" : "CH"); break;
        case "c": if (sig === "h") { agregar("CH"); i++; } else agregar(sig === "e" || sig === "i" ? "S" : "K"); break;
        case "l": if (sig === "l") { agregar("CH"); i++; } else agregar("L"); break;
        case "r": if (sig === "r") { agregar("RR"); i++; } else agregar(i === 0 ? "RR" : "R"); break;
        case "m": case "b": case "p": case "v": agregar("MBP"); break;
        case "f": agregar("FV"); break;
        case "s": case "z": agregar("S"); break;
        case "x": agregar("K"); agregar("S"); break;
        case "q": case "k": case "g": case "j": agregar("K"); break;
        case "w": agregar("U"); break;
        case "n": case "t": case "d": case "ñ": agregar("L"); break;
        default: break; // h muda, signos
      }
    }
  }
  return salida;
}

/** Energía por cuadros de 10 ms, tramo con voz y silencios internos de un AudioBuffer. */
export function analizarAudio(buffer) {
  const datos = buffer.getChannelData(0);
  const paso = Math.max(1, Math.round(buffer.sampleRate * PASO));
  const n = Math.floor(datos.length / paso);
  const energia = new Float32Array(n);
  let max = 0;
  for (let i = 0; i < n; i++) {
    let suma = 0;
    for (let j = i * paso, fin = j + paso; j < fin; j++) suma += datos[j] * datos[j];
    energia[i] = Math.sqrt(suma / paso);
    if (energia[i] > max) max = energia[i];
  }
  const umbral = Math.max(0.004, max * 0.06);
  let ini = 0;
  while (ini < n && energia[ini] < umbral) ini++;
  let fin = n - 1;
  while (fin > ini && energia[fin] < umbral) fin--;
  const silencios = [];
  let desde = -1;
  for (let i = ini; i <= fin; i++) {
    const callado = energia[i] < umbral;
    if (callado && desde < 0) desde = i;
    if (!callado && desde >= 0) {
      if (i - desde >= 5) silencios.push({ a: desde * PASO, b: i * PASO });
      desde = -1;
    }
  }
  return { ini: ini * PASO, fin: (fin + 1) * PASO, silencios, energia, max: max || 1, umbral };
}

/**
 * Reparte los sonidos de la frase en el tiempo. Las pausas fuertes (punto, coma) se anclan primero a los
 * silencios más cercanos a donde se esperan; luego los espacios entre palabras a silencios cortos; el resto
 * se reparte en proporción a la duración típica de cada sonido.
 */
export function planificar(texto, analisis) {
  const palabras = texto.trim().split(/\s+/).filter(Boolean);
  const unidades = [];
  const cortes = [];
  let w = 0;
  palabras.forEach((palabra, k) => {
    const sonidos = fonemas(palabra);
    if (!sonidos.length) sonidos.push(["reposo", 0.3]);
    for (const [forma, peso] of sonidos) {
      unidades.push({ forma, peso, palabra: k, w0: w, t0: 0, t1: 0 });
      w += peso;
    }
    if (k < palabras.length - 1) {
      const fuerza = /[.!?…:]["»”')\]]*$/.test(palabra) ? 2 : /[,;]["»”')\]]*$/.test(palabra) ? 1 : 0;
      cortes.push({ w, fuerza });
    }
  });
  const total = w || 1;
  const { ini, fin, silencios = [] } = analisis;
  const anclas = [{ w: 0, a: ini, b: ini }, { w: total, a: fin, b: fin }];
  const usados = new Set();
  for (const fuerza of [2, 1, 0]) {
    for (const corte of cortes) {
      if (corte.fuerza !== fuerza) continue;
      const j = anclas.findIndex((x) => x.w > corte.w);
      const lo = anclas[j - 1], hi = anclas[j];
      if (!lo || !hi || lo.w === corte.w) continue;
      const esperado = lo.b + ((corte.w - lo.w) / (hi.w - lo.w)) * (hi.a - lo.b);
      const tolerancia = fuerza === 2 ? 1.0 : fuerza === 1 ? 0.7 : 0.22;
      let mejor = -1, puntaje = Infinity;
      silencios.forEach((s, i) => {
        if (usados.has(i) || s.a <= lo.b || s.b >= hi.a) return;
        const dur = s.b - s.a;
        if (fuerza === 0 && dur < 0.07) return;
        const distancia = Math.abs((s.a + s.b) / 2 - esperado);
        const p = distancia - dur * (fuerza ? 1.5 : 0.5);
        if (distancia <= tolerancia && p < puntaje) { mejor = i; puntaje = p; }
      });
      if (mejor >= 0) {
        usados.add(mejor);
        anclas.splice(j, 0, { w: corte.w, a: silencios[mejor].a, b: silencios[mejor].b });
      }
    }
  }
  let j = 1;
  for (const u of unidades) {
    while (j < anclas.length - 1 && anclas[j].w <= u.w0) j++;
    const lo = anclas[j - 1], hi = anclas[j];
    const escala = Math.max(0.001, hi.a - lo.b) / Math.max(1e-6, hi.w - lo.w);
    u.t0 = lo.b + (u.w0 - lo.w) * escala;
    u.t1 = lo.b + (u.w0 + u.peso - lo.w) * escala;
  }
  const tiempos = palabras.map(() => ({ t0: Infinity, t1: 0 }));
  for (const u of unidades) {
    tiempos[u.palabra].t0 = Math.min(tiempos[u.palabra].t0, u.t0);
    tiempos[u.palabra].t1 = Math.max(tiempos[u.palabra].t1, u.t1);
  }
  return { unidades, palabras: tiempos, energia: analisis.energia || null, max: analisis.max || 1, umbral: analisis.umbral || 0 };
}

/** Descarga y decodifica el audio (URL, blob: incluida) y arma el plan de la frase. */
export async function prepararPlan(url, texto, ctx) {
  const respuesta = await fetch(url);
  const buffer = await ctx.decodeAudioData(await respuesta.arrayBuffer());
  return planificar(texto, analizarAudio(buffer));
}

/** Plan de una sola palabra sin audio (voz del navegador): duración estimada por sus sonidos. */
export function planDePalabra(palabra) {
  const duracion = Math.max(0.2, fonemas(palabra).reduce((s, [, p]) => s + p, 0) * 0.075);
  return planificar(palabra, { ini: 0, fin: duracion, silencios: [] });
}

const limitar = (x, a, b) => Math.min(b, Math.max(a, x));
const suavizado = (a, b, x) => { const t = limitar((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

/** Forma de boca en el instante t (s) del audio, con coarticulación y cierre en los silencios. */
export function formaEn(plan, t, salida = { ...FORMAS.reposo }) {
  const u = plan.unidades;
  Object.assign(salida, FORMAS.reposo);
  if (!u.length || t < u[0].t0 - 0.05 || t > u[u.length - 1].t1 + 0.05) return salida;
  let lo = 0, hi = u.length - 1;
  while (lo < hi) {
    const m = (lo + hi + 1) >> 1;
    if (u[m].t0 <= t) lo = m; else hi = m - 1;
  }
  const actual = u[lo], siguiente = u[lo + 1], anterior = u[lo - 1];
  // en una pausa (entre el último sonido y el siguiente) la boca descansa
  if (t > actual.t1 + 0.04 && (!siguiente || t < siguiente.t0 - 0.04)) return salida;
  const x = limitar((t - actual.t0) / Math.max(0.001, actual.t1 - actual.t0), 0, 1);
  const wSig = siguiente && siguiente.t0 - actual.t1 < 0.05 ? suavizado(0.55, 1, x) * 0.5 : 0;
  const wAnt = anterior && actual.t0 - anterior.t1 < 0.05 ? (1 - suavizado(0, 0.3, x)) * 0.5 : 0;
  const wAct = 1 - wSig - wAnt;
  const fa = FORMAS[actual.forma], fs = siguiente ? FORMAS[siguiente.forma] : fa, fp = anterior ? FORMAS[anterior.forma] : fa;
  for (const k of CLAVES) salida[k] = fa[k] * wAct + fs[k] * wSig + fp[k] * wAnt;

  if (plan.energia) {
    const e = plan.energia[limitar(Math.floor(t / PASO), 0, plan.energia.length - 1)];
    const voz = limitar((e - plan.umbral * 0.6) / (plan.umbral * 1.2), 0, 1);
    salida.abre *= voz * (0.65 + 0.5 * Math.min(1, (e / plan.max) * 1.8));
    // m/b/p y f/v se forman justo en un silencio corto (la oclusión): ahí no se apaga la presión de los labios
    for (const k of CLAVES) if (k !== "abre" && k !== "presion") salida[k] = FORMAS.reposo[k] + (salida[k] - FORMAS.reposo[k]) * voz;
  }
  return salida;
}

/** Respaldo sin texto: solo el volumen abre la boca (comportamiento anterior). */
export function formaPorVolumen(volumen, t, salida = { ...FORMAS.reposo }) {
  Object.assign(salida, FORMAS.reposo);
  salida.abre = limitar((volumen - 0.015) * 7, 0, 1);
  salida.ancho = (salida.abre > 0.5 ? 0.9 : 1) + Math.sin(t * 9) * 0.04 * salida.abre;
  salida.dientes = salida.abre * 0.6;
  return salida;
}

/** Índice de la palabra que suena en t (−1 antes de la primera). */
export function palabraEn(plan, t) {
  const p = plan.palabras;
  let k = -1;
  for (let i = 0; i < p.length && p[i].t0 <= t; i++) k = i;
  return k;
}
