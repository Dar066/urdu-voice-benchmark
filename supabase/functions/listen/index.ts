// Urdu Voice Lab: listening test gateway (Supabase Edge Function "listen")
// Checks the listener's secret link code, returns their session, and saves ratings.
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
const CLIP_RE = /^[0-9a-f]{8}$/;
const ACCENTS = new Set(["pk", "in", "unsure"]);

async function getListener(token: string) {
  if (!TOKEN_RE.test(token)) return null;
  const { data } = await db.from("listeners").select("listener_id, status").eq("token", token).maybeSingle();
  return data;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);

  try {
    const body = await req.json();
    const ls = await getListener(String(body.token || ""));
    if (!ls) return json({ error: "invalid link" }, 403);
    if (ls.status !== "active") return json({ error: "closed" }, 410);

    // --- session: who is this, and which clips are already rated? ---
    if (body.action === "session") {
      const { data, error } = await db.from("ratings").select("clip_id").eq("listener_id", ls.listener_id);
      if (error) throw error;
      return json({ listener_id: ls.listener_id, number: parseInt(ls.listener_id.slice(1)), done: data.map((r) => r.clip_id) });
    }

    // --- rate: save (or update) one rating ---
    if (body.action === "rate") {
      const clip_id = String(body.clip_id || "");
      const naturalness = Number(body.naturalness);
      const accent = String(body.accent || "");
      if (!CLIP_RE.test(clip_id) || !(naturalness >= 1 && naturalness <= 5) || !Number.isInteger(naturalness)
          || !ACCENTS.has(accent) || typeof body.wrong_word !== "boolean") {
        return json({ error: "bad rating" }, 400);
      }
      const { error } = await db.from("ratings").upsert({
        listener_id: ls.listener_id, clip_id, naturalness, accent, wrong_word: body.wrong_word,
        plays: Number.isInteger(body.plays) ? body.plays : null,
      }, { onConflict: "listener_id,clip_id" });
      if (error) throw error;
      return json({ ok: true });
    }

    // --- comment: optional free-text feedback at the end ---
    if (body.action === "comment") {
      const text = String(body.comment || "").trim();
      if (!text || text.length > 2000) return json({ error: "bad comment" }, 400);
      const { error } = await db.from("listener_comments").insert({ listener_id: ls.listener_id, comment: text });
      if (error) throw error;
      return json({ ok: true });
    }

    return json({ error: "bad action" }, 400);
  } catch (e) {
    console.error(e);
    return json({ error: "server error" }, 500);
  }
});
