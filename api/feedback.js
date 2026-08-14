// POST /api/feedback: stores user feedback in Supabase (service key stays
// server-side; the table has RLS on with no policies, so only this function
// can write). Body: { message, rating?, cc?, city?, ha?, lang?, hash? }
export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  const { message, rating, cc, city, ha, lang, hash, website } = req.body ?? {};
  if (website) return res.status(204).end(); // honeypot: bots fill hidden fields
  if (typeof message !== "string" || !message.trim() || message.length > 2000)
    return res.status(400).json({ error: "message required (1-2000 chars)" });
  const row = {
    message: message.trim(),
    rating: Number.isInteger(rating) && rating >= 1 && rating <= 5 ? rating : null,
    cc: typeof cc === "string" ? cc.slice(0, 2) : null,
    city: typeof city === "string" ? city.slice(0, 80) : null,
    ha: typeof ha === "number" && isFinite(ha) ? Math.round(ha * 10) / 10 : null,
    lang: typeof lang === "string" ? lang.slice(0, 5) : null,
    hash: typeof hash === "string" ? hash.slice(0, 2000) : null,
  };
  const r = await fetch(`${process.env.SUPABASE_URL}/rest/v1/replantio_feedback`, {
    method: "POST",
    headers: {
      apikey: process.env.SUPABASE_SERVICE_KEY,
      Authorization: `Bearer ${process.env.SUPABASE_SERVICE_KEY}`,
      "Content-Type": "application/json",
      Prefer: "return=minimal",
    },
    body: JSON.stringify(row),
  });
  if (!r.ok) return res.status(502).json({ error: "storage failed" });
  return res.status(204).end();
}
