// Supabase Edge Function: "lead-ai"
// EINE Funktion für ZWEI Aufgaben des Alzinger Vertriebs-CRM:
//   A) Lead-Suche:      bekommt { was, wo }   -> liefert { leads: [...] }   (Claude + Web-Suche)
//   B) Visitenkarte:    bekommt { image }     -> liefert { contact: {...} } (Claude-Vision)
// Der Anthropic-Key bleibt serverseitig. Die App ruft IMMER diese eine Funktion auf.
//
// EINRICHTEN (einmalig, im Supabase-Dashboard):
//  1. Edge Functions -> Funktion "lead-ai" (oder "lead-ai-") -> Code: DIESEN Code einfügen.
//  2. "Verify JWT" AUSschalten (Enforce JWT verification = off).
//  3. Secrets: ANTHROPIC_API_KEY = sk-ant-... , CRM_SECRET = dasselbe Passwort wie in der App.
//  4. Deploy.

const MODEL = "claude-opus-4-8";
// URL gestückelt, damit sie beim Kopieren nicht automatisch verlinkt wird.
const ANTHROPIC_URL = "https" + "://api.anthropic" + ".c" + "om/v1/messages";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-crm-secret",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(obj: unknown, status = 200): Response {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

/* ============================ A) LEAD-SUCHE ============================ */

function extractLeads(t: string): any[] | null {
  const m = t.match(/\[\s*\{[\s\S]*\}\s*\]/);
  if (m) { try { const a = JSON.parse(m[0]); if (Array.isArray(a)) return a; } catch (_) { /* weiter */ } }
  try { const a = JSON.parse(t.trim()); if (Array.isArray(a)) return a; } catch (_) { /* weiter */ }
  const start = t.indexOf("[");
  if (start >= 0) {
    const lastObj = t.lastIndexOf("}");
    if (lastObj > start) {
      const repaired = t.slice(start, lastObj + 1) + "]";
      try { const a = JSON.parse(repaired); if (Array.isArray(a)) return a; } catch (_) { /* weiter */ }
    }
  }
  return null;
}

async function research(apiKey: string, was: string, wo: string): Promise<unknown> {
  const prompt =
`Du bist Vertriebs-Rechercheur für Alzinger Maschinenbau. Verkauft wird die mobile
Sternsiebanlage Lepton 5100 – ideale Kunden sind Betriebe in Kompostierung, Recycling/
Entsorgung, Erden-/Substratwerke, Steinbruch/Schotter, Garten-/Landschaftsbau, Biogas.

Suche im Web nach REALEN Firmen, die zu "${was}" in der Region "${wo}" passen,
und ermittle die wichtigsten Eckdaten pro Firma (Website/Impressum, ggf. Presse).
WICHTIG – arbeite ZÜGIG: nutze nur WENIGE, gezielte Web-Suchen (max. ~4) und antworte
schnell. Die App ruft dich automatisch mehrfach auf und sammelt weitere Firmen –
EINE Runde muss daher nur die besten Treffer liefern, NICHT alles auf einmal.
Antworte AUSSCHLIESSLICH mit einem JSON-Array (kein Fließtext, kein Markdown, keine \`\`\`).
Jedes Element exakt so:
{"firma":"","strasse":"","plz":"","ort":"","land":"DE","web":"","tel":"","email":"","geschaeftsfuehrer":"","betriebsleiter":"","jahresmenge":"","siebtechnik":"","news":"","quelle":""}
- land als Ländercode (DE/AT/CH/...).
- ort und plz sind WICHTIG: ort (Stadt/Gemeinde) IMMER ausfüllen; plz möglichst immer mitliefern.
- email: allgemeine Kontakt-/Info-Adresse, wenn auffindbar (z.B. aus dem Impressum).
- geschaeftsfuehrer / betriebsleiter: Namen, wenn auffindbar.
- jahresmenge: verarbeitete Menge pro Jahr mit Einheit, falls öffentlich, sonst "".
- siebtechnik: NUR "Trommelsieb" oder "Sternsieb", wenn klar erkennbar; sonst "" (nicht raten!).
- news: ein relevanter aktueller Punkt mit Jahr, sonst "".
- quelle: kurz, woher die Infos stammen.
- WICHTIG: Unbekannte Felder als leerer String "". Nichts erfinden – lieber leer lassen.
- 6–8 Firmen pro Antwort genügen. Nur echte, im Web auffindbare Betriebe (keine Dubletten).`;

  const base = {
    model: MODEL,
    max_tokens: 9000,
    tools: [{ type: "web_search_20260209", name: "web_search", max_uses: 5 }],
  };

  let messages: unknown[] = [{ role: "user", content: prompt }];
  let data: any = null;
  for (let i = 0; i < 10; i++) {
    const r = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
      body: JSON.stringify({ ...base, messages }),
    });
    if (!r.ok) {
      const t = await r.text();
      return { leads: [], error: "anthropic " + r.status, detail: t.slice(0, 300) };
    }
    data = await r.json();
    if (data.stop_reason === "pause_turn") {
      messages = [...messages, { role: "assistant", content: data.content }];
      continue;
    }
    break;
  }

  let text = (data?.content || [])
    .filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n").trim();
  text = text.replace(/```json/gi, "").replace(/```/g, "");

  const leads = extractLeads(text);
  if (leads === null) {
    return { leads: [], debug: { stop_reason: data?.stop_reason || null, text_len: text.length, sample: text.slice(0, 500) } };
  }
  return { leads };
}

/* ============================ B) VISITENKARTE ============================ */

const CARD_PROMPT =
`Du extrahierst Kontaktdaten von einer abfotografierten VISITENKARTE.
Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Fließtext, kein Markdown, keine \`\`\`),
exakt mit diesen Feldern:
{"firma":"","anrede":"","vorname":"","nachname":"","position":"","strasse":"","plz":"","ort":"","land":"DE","tel":"","mobil":"","mail":"","web":"","ustid":""}
Regeln:
- land als Ländercode (DE/AT/CH/...). Sonst "DE".
- anrede: akademische/höfliche Anrede falls vorhanden (z.B. "Dr.", "Herr", "Frau"); sonst "".
- position: Funktion/Titel auf der Karte (z.B. "Geschäftsführer"); sonst "".
- tel = Festnetz, mobil = Handynummer (Mobil/Mobile/Handy/M: oder +.. 1xx -> mobil, sonst tel).
- mail = E-Mail, web = Webseite (ohne "http://"). strasse mit Hausnummer; plz und ort getrennt.
- Unbekannte Felder als leerer String "". NICHTS erfinden – nur was auf der Karte steht.`;

async function scanCard(apiKey: string, image: string): Promise<Response> {
  const m = image.match(/^data:([^;]+);base64,([\s\S]*)$/);
  const media_type = m ? m[1] : "image/jpeg";
  const dataB64 = m ? m[2] : image;
  const r = await fetch(ANTHROPIC_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 1200,
      messages: [{
        role: "user",
        content: [
          { type: "image", source: { type: "base64", media_type, data: dataB64 } },
          { type: "text", text: CARD_PROMPT },
        ],
      }],
    }),
  });
  if (!r.ok) { const t = await r.text(); return json({ error: "anthropic " + r.status, detail: t.slice(0, 300) }, 502); }
  const data: any = await r.json();
  let text = (data?.content || [])
    .filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n").trim()
    .replace(/```json/gi, "").replace(/```/g, "");
  let contact: any = null;
  const mm = text.match(/\{[\s\S]*\}/);
  if (mm) { try { contact = JSON.parse(mm[0]); } catch (_) { /* weiter */ } }
  if (!contact) { try { contact = JSON.parse(text); } catch (_) { /* weiter */ } }
  if (!contact || typeof contact !== "object") return json({ contact: {}, debug: { sample: text.slice(0, 400) } });
  return json({ contact });
}

/* ============================ HINTERGRUND-JOB (für strenge Proxies) ============================ */
// Schreibt das Ergebnis in die Tabelle public.ai_jobs (per Service-Role-Key). Die App holt es
// dann per normaler DB-Abfrage ab -> funktioniert auch hinter Proxies, die lange Antworten kappen.
async function saveJob(jobId: string, result: unknown): Promise<void> {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) return;
  await fetch(url + "/rest/v1/ai_jobs", {
    method: "POST",
    headers: {
      apikey: key, Authorization: "Bearer " + key, "Content-Type": "application/json",
      Prefer: "resolution=merge-duplicates,return=minimal",
    },
    body: JSON.stringify({ id: jobId, result, done: true }),
  }).catch(() => {});
}

/* ============================ ROUTER ============================ */

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST erforderlich" }, 405);

  const apiKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!apiKey) return json({ error: "ANTHROPIC_API_KEY fehlt (Secret setzen)" }, 500);

  const body = await req.json().catch(() => ({}));
  // Secret aus Header ODER Body akzeptieren: der "einfache" Aufruf (ohne CORS-Vorabpruefung)
  // kann keinen x-crm-secret-Header senden und liefert das Secret daher im Body mit.
  const secret = Deno.env.get("CRM_SECRET") || "";
  const provided = req.headers.get("x-crm-secret") || (body && body.secret) || "";
  if (secret && provided !== secret) return json({ error: "unauthorized" }, 401);

  // B) Visitenkarte: kurze Antwort, kein Streaming nötig.
  if (body && typeof body.image === "string" && body.image) {
    try { return await scanCard(apiKey, body.image); }
    catch (e) { return json({ error: String((e as Error)?.message || e) }, 500); }
  }

  // A) Lead-Suche
  const was = body?.was, wo = body?.wo, jobId = body?.jobId;
  if (!was || !wo) return json({ error: "Bitte was+wo (Lead-Suche) oder image (Visitenkarte) senden" }, 400);

  // A1) Mit jobId -> Hintergrund-Job: SOFORT antworten, Ergebnis kommt in die Tabelle ai_jobs.
  if (jobId) {
    const work = (async () => {
      let out: unknown;
      try { out = await research(apiKey, String(was), String(wo)); }
      catch (e) { out = { leads: [], error: String((e as Error)?.message || e) }; }
      await saveJob(String(jobId), out);
    })();
    try { (globalThis as any).EdgeRuntime?.waitUntil?.(work); } catch (_) { /* lokal egal */ }
    return json({ ok: true, jobId });
  }

  // A2) Ohne jobId -> alte Streaming-Variante (abwaertskompatibel).

  const enc = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try { controller.enqueue(enc.encode(" ")); } catch (_) { /* sofort, gegen kurze Proxy-Timeouts */ }
      const keepalive = setInterval(() => { try { controller.enqueue(enc.encode(" ")); } catch (_) { /* zu */ } }, 2000);
      let out: unknown;
      try { out = await research(apiKey, String(was), String(wo)); }
      catch (e) { out = { leads: [], error: String((e as Error)?.message || e) }; }
      clearInterval(keepalive);
      try { controller.enqueue(enc.encode("\n" + JSON.stringify(out))); } catch (_) { /* ignore */ }
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { ...cors, "Content-Type": "application/json" } });
});
