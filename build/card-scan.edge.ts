// Supabase Edge Function: "card-scan"
// Wertet ein Foto einer VISITENKARTE per Claude-Vision aus und gibt die Kontaktdaten
// als JSON zurück. Gleiches Muster wie "lead-ai": Anthropic-Key bleibt serverseitig.
//
// EINRICHTEN (einmalig, im Supabase-Dashboard):
//  1. Edge Functions -> "Deploy a new function" -> Name: card-scan  (diesen Code einfügen)
//  2. "Verify JWT" AUSschalten (Enforce JWT verification = off).
//  3. Secrets (teilt sich dieselben wie lead-ai):
//       ANTHROPIC_API_KEY = sk-ant-...
//       CRM_SECRET        = dasselbe Passwort wie in der App
//  4. Deploy. Aufruf-URL: https://<projekt>.supabase.co/functions/v1/card-scan
//
// Die App schickt { image: "data:image/jpeg;base64,..." } + Header x-crm-secret
// und bekommt { contact: { firma, vorname, ... } }.

const MODEL = "claude-opus-4-8";
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

const PROMPT =
`Du extrahierst Kontaktdaten von einer abfotografierten VISITENKARTE.
Gib AUSSCHLIESSLICH ein JSON-Objekt zurück (kein Fließtext, kein Markdown, keine \`\`\`),
exakt mit diesen Feldern:
{"firma":"","anrede":"","vorname":"","nachname":"","position":"","strasse":"","plz":"","ort":"","land":"DE","tel":"","mobil":"","mail":"","web":"","ustid":""}
Regeln:
- land als Ländercode (DE/AT/CH/...). Wenn nur an der Telefonvorwahl/Sprache erkennbar, sinnvoll wählen, sonst "DE".
- anrede: akademische/höfliche Anrede falls vorhanden (z.B. "Dr.", "Herr", "Frau"); sonst "".
- position: Funktion/Titel auf der Karte (z.B. "Geschäftsführer", "Vertrieb"); sonst "".
- tel = Festnetz, mobil = Handynummer. Wenn eine Nummer klar als Mobil/Mobile/Handy/M: markiert ist
  oder mit +.. 1xx beginnt -> mobil, sonst -> tel. Nummern mit Leer-/Bindestrichen so lassen.
- mail = E-Mail-Adresse, web = Webseite (ohne "http://").
- strasse mit Hausnummer; plz und ort getrennt.
- Unbekannte Felder als leerer String "". NICHTS erfinden – nur was auf der Karte steht.`;

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST erforderlich" }, 405);

  try {
    const secret = Deno.env.get("CRM_SECRET") || "";
    if (secret && req.headers.get("x-crm-secret") !== secret) return json({ error: "unauthorized" }, 401);
    const apiKey = Deno.env.get("ANTHROPIC_API_KEY");
    if (!apiKey) return json({ error: "ANTHROPIC_API_KEY fehlt (Secret setzen)" }, 500);

    const body = await req.json().catch(() => ({}));
    const image = body?.image;
    if (!image || typeof image !== "string") return json({ error: "Bitte image (data-URI) senden" }, 400);

    const m = image.match(/^data:([^;]+);base64,([\s\S]*)$/);
    const media_type = m ? m[1] : "image/jpeg";
    const dataB64 = m ? m[2] : image;

    const r = await fetch(ANTHROPIC_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 1200,
        messages: [{
          role: "user",
          content: [
            { type: "image", source: { type: "base64", media_type, data: dataB64 } },
            { type: "text", text: PROMPT },
          ],
        }],
      }),
    });
    if (!r.ok) {
      const t = await r.text();
      return json({ error: "anthropic " + r.status, detail: t.slice(0, 300) }, 502);
    }
    const data: any = await r.json();
    let text = (data?.content || [])
      .filter((b: any) => b.type === "text")
      .map((b: any) => b.text)
      .join("\n")
      .trim()
      .replace(/```json/gi, "").replace(/```/g, "");

    // JSON-Objekt herausziehen (auch wenn etwas Text drumherum steht).
    let contact: any = null;
    const mm = text.match(/\{[\s\S]*\}/);
    if (mm) { try { contact = JSON.parse(mm[0]); } catch (_) { /* weiter */ } }
    if (!contact) { try { contact = JSON.parse(text); } catch (_) { /* weiter */ } }
    if (!contact || typeof contact !== "object") {
      return json({ contact: {}, debug: { sample: text.slice(0, 400) } });
    }
    return json({ contact });
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500);
  }
});
