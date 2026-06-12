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

/* ============================ C) NOTIZ -> KONTAKT + VERLAUF ============================ */
// Wertet eine Vertriebs-Notiz (z. B. aus OneNote) aus: Kontaktdaten + datierter Verlauf.
const NOTE_PROMPT =
`Du erhältst eine Vertriebs-Notiz (z. B. aus OneNote) zu EINER Firma. Extrahiere
1) die Kontaktdaten und 2) den chronologischen Verlauf als Aktivitäten.
Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Fließtext, kein Markdown, keine \`\`\`):
{"contact":{"firma":"","anrede":"","vorname":"","nachname":"","position":"","strasse":"","plz":"","ort":"","bundesland":"","land":"DE","tel":"","mobil":"","mail":"","web":""},
 "activities":[{"date":"YYYY-MM-DD","type":"notiz","note":""}]}
Regeln:
- firma: Firmenname (oft die Überschrift). vorname/nachname: Ansprechpartner. position: Funktion, falls genannt.
- bundesland: deutsches Bundesland, aus Ort/Adresse ableiten falls möglich, sonst "".
- land als Ländercode (DE/AT/CH/...).
- activities: JEDE datierte Zeile = ein Eintrag. date als YYYY-MM-DD
  (deutsche Datumsangaben wie "23.09.24" -> "2024-09-23", "10.03.2026" -> "2026-03-10").
  type: einer von "anruf","mailout","mailin","besuch","angebot","notiz" – passend:
  telefoniert/angerufen -> anruf; Mail/Werbemail RAUS -> mailout; Mail/Antwort REIN -> mailin;
  vor Ort/Besuch/Termin -> besuch; Angebot gesendet -> angebot; sonst -> notiz.
  note: der Inhalt der Zeile OHNE das Datum, inhaltlich vollständig.
- Reihenfolge der activities chronologisch (älteste zuerst).
- Unbekannte Felder als "". NICHTS erfinden – nur was in der Notiz steht.`;
async function parseNote(apiKey: string, notiz: string): Promise<Response> {
  const r = await fetch(ANTHROPIC_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({
      model: MODEL, max_tokens: 4000,
      messages: [{ role: "user", content: NOTE_PROMPT + "\n\n--- NOTIZ ---\n" + notiz.slice(0, 12000) }],
    }),
  });
  if (!r.ok) { const t = await r.text(); return json({ error: "anthropic " + r.status, detail: t.slice(0, 300) }, 502); }
  const data: any = await r.json();
  let text = (data?.content || []).filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n").trim()
    .replace(/```json/gi, "").replace(/```/g, "");
  let obj: any = null;
  const mm = text.match(/\{[\s\S]*\}/);
  if (mm) { try { obj = JSON.parse(mm[0]); } catch (_) { /* weiter */ } }
  if (!obj) { try { obj = JSON.parse(text); } catch (_) { /* weiter */ } }
  if (!obj || typeof obj !== "object") return json({ contact: {}, activities: [], debug: { sample: text.slice(0, 400) } });
  return json({ contact: obj.contact || {}, activities: Array.isArray(obj.activities) ? obj.activities : [] });
}

/* ============================ E) FIRMA NACHSCHLAGEN (ein Kontakt ergänzen) ============================ */
// Schlägt EINE bestimmte, bereits bekannte Firma im Web nach und liefert deren Kontaktdaten.
async function enrichCompany(apiKey: string, p: any): Promise<Response> {
  const prompt =
`Du recherchierst die Daten EINER bestimmten, bereits bekannten Firma – das ist KEIN Branchen-Suchlauf.
VORGEHEN: Finde die offizielle WEBSITE dieser Firma und LIES sie aus – vor allem die Seiten
"Impressum", "Kontakt" und "Über uns". Trage ALLES Wichtige für einen Vertriebskontakt zusammen.
Firma: "${p?.firma || ""}"${p?.ort ? `\nOrt: ${p.ort}` : ""}${p?.land ? `\nLand: ${p.land}` : ""}${p?.web ? `\nWebsite (Hinweis, bevorzugt zuerst aufrufen): ${p.web}` : ""}${p?.plz ? `\nPLZ: ${p.plz}` : ""}
Antworte AUSSCHLIESSLICH mit EINEM JSON-Objekt (kein Fließtext, kein Markdown, keine \`\`\`):
{"firma":"","strasse":"","plz":"","ort":"","land":"","web":"","tel":"","email":"","ustid":"",
 "anrede":"","vorname":"","nachname":"","position":"","ap_mail":"","ap_mobil":"",
 "geschaeftsfuehrer":"","betriebsleiter":"","jahresmenge":"","siebtechnik":"","info":"","quelle":"","confidence":""}
Regeln:
- NUR Daten DIESER Firma. Findest du sie nicht eindeutig, ALLE Felder leer und confidence:"keine".
- land als Ländercode (DE/AT/CH/...). web ohne "https://". strasse mit Hausnummer; plz und ort getrennt.
- tel = Festnetz/Zentrale, email = allgemeine Kontaktadresse (Impressum). ustid = USt-IdNr./MwSt-Nr., falls genannt.
- anrede/vorname/nachname/position/ap_mail/ap_mobil = EIN konkreter Ansprechpartner (z. B. Geschäftsführer
  oder Vertrieb), wenn auf der Website auffindbar – sonst leer.
- geschaeftsfuehrer/betriebsleiter: Namen, wenn genannt. siebtechnik: nur "Trommelsieb"/"Sternsieb" wenn klar, sonst "".
- info: 1–2 kurze Sätze, was die Firma macht (Branche/Tätigkeit) – für die Notiz.
- quelle: kurz, woher (z. B. "Impressum berom.ch"). confidence: "hoch" (Website/Impressum gefunden) oder "niedrig".
- Unbekannte Felder als "". Nichts erfinden.`;
  const base = { model: MODEL, max_tokens: 3000, tools: [{ type: "web_search_20260209", name: "web_search", max_uses: 6 }] };
  let messages: unknown[] = [{ role: "user", content: prompt }];
  let data: any = null;
  for (let i = 0; i < 8; i++) {
    const r = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
      body: JSON.stringify({ ...base, messages }),
    });
    if (!r.ok) { const t = await r.text(); return json({ error: "anthropic " + r.status, detail: t.slice(0, 300) }, 502); }
    data = await r.json();
    if (data.stop_reason === "pause_turn") { messages = [...messages, { role: "assistant", content: data.content }]; continue; }
    break;
  }
  let text = (data?.content || []).filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n").trim()
    .replace(/```json/gi, "").replace(/```/g, "");
  let obj: any = null;
  const mm = text.match(/\{[\s\S]*\}/);
  if (mm) { try { obj = JSON.parse(mm[0]); } catch (_) { /* weiter */ } }
  if (!obj) { try { obj = JSON.parse(text); } catch (_) { /* weiter */ } }
  if (!obj || typeof obj !== "object") return json({ confidence: "keine", debug: { sample: text.slice(0, 400) } });
  return json(obj);
}

/* ============================ D) KI-ANTWORTVORSCHLAG (E-Mail) ============================ */
// Entwirft eine KURZE, bodenständige Antwort – im Ton eines Maschinenbauers, nicht geschwollen.
const REPLY_PROMPT =
`Du arbeitest im Vertrieb der Alzinger Maschinenbau GmbH und verkaufst die mobile
Sternsiebanlage "Lepton 5100". Schreib eine Antwort-E-Mail auf die eingegangene Nachricht,
in der Sprache der Mail (Standard: Deutsch), per Sie.
WICHTIG – der TON: kurz, einfach, bodenständig – so wie ein Maschinenbauer schreibt.
Sachlich, freundlich, direkt, auf den Punkt. NICHT geschwollen, kein Werbe- oder Behördendeutsch.
Regeln:
- HÖCHSTENS 3–4 kurze Sätze. Lieber zu kurz als zu lang.
- Einfache, klare Wörter. Vermeide Phrasen wie "Leistungsfähigkeit präsentieren",
  "Rahmenbedingungen abstimmen", "würde mich sehr freuen", "im Zuge dessen",
  "gerne stehen wir Ihnen zur Verfügung", "zögern Sie nicht".
- HÖCHSTENS EINE Rückfrage, und nur wenn wirklich nötig.
- KEINE Grußformel, KEIN Name, KEINE Signatur am Ende. Hör nach dem letzten inhaltlichen
  Satz auf – Gruß und Signatur hängt das Programm selbst an.
- Nichts erfinden (keine Preise/Termine zusagen, die nicht genannt wurden).
Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Fließtext, kein Markdown, keine \`\`\`):
{"subject":"","body":""}
- subject: kurzer, passender Betreff. Bei vorhandenem Original-Betreff "Re: ..." nutzen.
- body: nur der Nachrichtentext MIT Anrede (z. B. "Sehr geehrte Damen und Herren," oder mit Namen,
  falls bekannt), echte Zeilenumbrüche (\\n), OHNE Grußformel/Name am Ende.`;
async function draftReply(apiKey: string, p: any): Promise<Response> {
  const ctx = [
    p?.firma ? "Firma: " + p.firma : "",
    p?.name ? "Ansprechpartner: " + p.name : "",
    p?.subject ? "Original-Betreff: " + p.subject : "",
    "--- EINGEGANGENE NACHRICHT ---",
    String(p?.text || "").slice(0, 8000),
  ].filter(Boolean).join("\n");
  const r = await fetch(ANTHROPIC_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" },
    body: JSON.stringify({
      model: MODEL, max_tokens: 2000,
      messages: [{ role: "user", content: REPLY_PROMPT + "\n\n" + ctx }],
    }),
  });
  if (!r.ok) { const t = await r.text(); return json({ error: "anthropic " + r.status, detail: t.slice(0, 300) }, 502); }
  const data: any = await r.json();
  let text = (data?.content || []).filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n").trim()
    .replace(/```json/gi, "").replace(/```/g, "");
  let obj: any = null;
  const mm = text.match(/\{[\s\S]*\}/);
  if (mm) { try { obj = JSON.parse(mm[0]); } catch (_) { /* weiter */ } }
  if (!obj) { try { obj = JSON.parse(text); } catch (_) { /* weiter */ } }
  if (!obj || typeof obj !== "object") return json({ subject: "", body: "", debug: { sample: text.slice(0, 400) } });
  return json({ subject: String(obj.subject || ""), body: String(obj.body || "") });
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

  // C) Notiz/OneNote -> Kontakt + Verlauf.
  if (body && typeof body.notiz === "string" && body.notiz.trim()) {
    try { return await parseNote(apiKey, body.notiz); }
    catch (e) { return json({ error: String((e as Error)?.message || e) }, 500); }
  }

  // D) KI-Antwortvorschlag auf eine eingegangene E-Mail.
  if (body && body.mailReply && typeof body.mailReply === "object") {
    try { return await draftReply(apiKey, body.mailReply); }
    catch (e) { return json({ error: String((e as Error)?.message || e) }, 500); }
  }

  // E) Eine bestimmte Firma nachschlagen (Kontakt ergänzen).
  if (body && body.enrich && typeof body.enrich === "object") {
    try { return await enrichCompany(apiKey, body.enrich); }
    catch (e) { return json({ error: String((e as Error)?.message || e) }, 500); }
  }

  // A) Lead-Suche
  const was = body?.was, wo = body?.wo, jobId = body?.jobId;
  if (!was || !wo) return json({ error: "Bitte was+wo (Lead-Suche), image (Visitenkarte) oder notiz senden" }, 400);

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
