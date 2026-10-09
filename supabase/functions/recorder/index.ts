// Urdu Voice Lab: upload gateway (Supabase Edge Function "recorder")
// Checks the speaker's secret link code, then saves each take. Never overwrites.
import { createClient } from "npm:@supabase/supabase-js@2";

const ALLOWED_ORIGIN = "https://YOUR-SITE.vercel.app";
const cors = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});

const TOKEN_RE = /^[0-9a-f]{32}$/;
const ROW_RE = /^(CONSENT|FREE0[1-3]|[A-Z]{3}[0-9]{2})$/;
const TYPES: Record<string, string> = { "audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a" };
const MAX_BYTES = 3 * 1024 * 1024;

async function getSpeaker(token: string) {
  if (!TOKEN_RE.test(token)) return null;
  const { data } = await db.from("speakers").select("speaker_id, condition, status").eq("token", token).maybeSingle();
  return data;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);

  try {
    // --- session: who is this link, and what is already recorded? ---
    if ((req.headers.get("content-type") || "").includes("application/json")) {
      const { action, token } = await req.json();
      if (action !== "session") return json({ error: "bad action" }, 400);
      const sp = await getSpeaker(String(token || ""));
      if (!sp) return json({ error: "invalid link" }, 403);
      if (sp.status !== "active") return json({ error: "closed" }, 410);
      const { data, error } = await db.from("recordings").select("row_id")
        .eq("speaker_id", sp.speaker_id).eq("condition", sp.condition).eq("is_final", true);
      if (error) throw error;
      return json({ speaker_id: sp.speaker_id, condition: sp.condition, done: [...new Set(data.map((r) => r.row_id))] });
    }

    // --- upload: save one take ---
    const form = await req.formData();
    const sp = await getSpeaker(String(form.get("token") || ""));
    if (!sp) return json({ error: "invalid link" }, 403);
    if (sp.status !== "active") return json({ error: "closed" }, 410);

    const row_id = String(form.get("row_id") || "");
    if (!ROW_RE.test(row_id)) return json({ error: "bad row id" }, 400);

    const file = form.get("file");
    if (!(file instanceof File)) return json({ error: "no file" }, 400);
    const baseType = (file.type || "").split(";")[0];
    const ext = TYPES[baseType];
    if (!ext) return json({ error: "unsupported audio type" }, 415);
    if (file.size === 0 || file.size > MAX_BYTES) return json({ error: "bad file size" }, 413);

    const { data: prev, error: prevErr } = await db.from("recordings").select("take")
      .eq("speaker_id", sp.speaker_id).eq("condition", sp.condition).eq("row_id", row_id)
      .order("take", { ascending: false }).limit(1);
    if (prevErr) throw prevErr;
    const take = (prev?.[0]?.take || 0) + 1;
    const path = `${sp.speaker_id}/${sp.speaker_id}_${row_id}_${sp.condition}_t${take}.${ext}`;

    const up = await db.storage.from("recordings").upload(path, file, { contentType: baseType, upsert: false });
    if (up.error) throw up.error;

    const str = (k: string, n = 2000) => String(form.get(k) || "").slice(0, n);
    const num = (k: string) => { const v = parseFloat(str(k, 20)); return Number.isFinite(v) ? v : null; };

    const old = await db.from("recordings").update({ is_final: false })
      .eq("speaker_id", sp.speaker_id).eq("condition", sp.condition).eq("row_id", row_id);
    if (old.error) throw old.error;

    const ins = await db.from("recordings").insert({
      speaker_id: sp.speaker_id, condition: sp.condition, row_id, take, file_path: path,
      category: str("category", 20), text_read: str("text_read"), entity: str("entity", 200),
      duration_s: num("duration_s"), retakes: num("retakes"), clipped: str("clipped", 5) === "yes", is_final: true,
    });
    if (ins.error) throw ins.error;

    return json({ ok: true, take, path });
  } catch (e) {
    console.error(e);
    return json({ error: "server error" }, 500);
  }
});
