export function clavePiso(value = "") {
  const t = String(value).trim().toLowerCase();
  if (/^(pb|planta baja)$/.test(t)) return "PB";
  if (/^(s|ss)$/.test(t) || /s[oó]tano|parqueo/.test(t)) return "S";
  const numeric = t.match(/^(?:piso\s*)?([1-9]\d*)(?:\s*piso)?$/);
  if (numeric) return Number(numeric[1]) >= 5 ? "5" : numeric[1];
  const labels = ["primer", "segundo", "tercer", "cuarto", "quinto"];
  const index = labels.findIndex(word => t.includes(word));
  return index === -1 ? null : String(index + 1);
}

export function tarjetasDeEvidencia(sources) {
  const tipos = { venue: "lugar", product: "producto", promotion: "promocion", event: "evento", faq: "info" };
  return (sources || []).map((source) => {
    const a = source.attributes || {};
    const fecha = a.starts_at ? new Intl.DateTimeFormat("es-BO", { timeZone: "America/La_Paz", dateStyle: "medium", timeStyle: "short" }).format(new Date(a.starts_at)) : "";
    return {
      id: source.id, tipo: tipos[source.kind] || "info", nombre: source.title, titulo: source.title,
      foto: a.image_url || "",
      categoria: a.category || a.scope || a.condition || "Información del Paseo",
      ubicacion: { piso: a.floor || "", local: a.unit || "", sector: a.area || "", referencia: a.data_origin === 'synthetic_demo' ? '' : a.reference || "" },
      fuente_url: a.data_origin === "synthetic_demo" ? "/catalog/demo" : /^https?:\/\//.test(source.source_url || "") ? source.source_url : "",
      precio_bs: a.price_bs, stock: a.stock, tienda: { nombre: a.venue_name || a.venue_id || "" },
      descripcion: a.benefit || a.description || "", condiciones: a.terms || "",
      fecha, lugar: a.location || "", pregunta: source.title, respuesta: a.answer || a.scope || a.condition || "Consulta la fuente publicada.",
      abierto_ahora: a.open_now, horario: a.schedule_today || (a.opens ? `${a.opens}–${a.closes}` : ""),
      demo: a.data_origin === 'synthetic_demo',
      verificacion: a.data_origin === 'synthetic_demo' ? "Demo · precio estimado" : a.review_status === "approved" ? "Revisada" : "Fuente disponible",
      verificado_en: a.verified_at || a.observed_at || (a.data_origin === "synthetic_demo" ? source.updated_at : ""), vence: source.expires_at || a.ends_at || "",
      torre: a.tower || "", descripcion_evento: source.kind === 'event' ? a.description || '' : '',
    };
  });
}
