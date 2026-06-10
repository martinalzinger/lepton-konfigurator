// Supabase Edge Function: "lead-ai"
// KI-Lead-Suche für das Alzinger Vertriebs-CRM. Hält den Anthropic-API-Key sicher
// serverseitig und ruft Claude mit Web-Suche auf, um echte Firmen-Leads zu finden.
//
// EINRICHTEN (einmalig, im Supabase-Dashboard):
//  1. Edge Functions -> "Deploy a new function" -> Name: lead-ai
//     (oder per CLI: supabase functions new lead-ai)  Diesen Code einfügen.
//  2. WICHTIG: "Verify JWT" AUSschalten (Enforce JWT verification = off),
//     sonst lehnt die Funktion den Publishable-Key ab.
//  3. Secrets setzen (Edge Functions -> Manage secrets / Settings):
//       ANTHROPIC_API_KEY  = dein Anthropic-Key (sk-ant-...)
//       CRM_SECRET         = ein selbst ausgedachtes Passwort (auch in der App eintragen)
//  4. Deploy. Aufruf-URL: https://<projekt>.supabase.co/functions/v1/lead-ai
//
// Die App schickt { was, wo } und den Header x-crm-secret und bekommt { leads: [...] }.

const MODEL = "claude-opus-4-8";
// URL gestückelt, damit sie beim Kopieren nicht automatisch in <…> verlinkt wird.
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

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "POST erforderlich" }, 405);

  try {
    const secret = Deno.env.get("CRM_SECRET") || "";
    if (secret && req.headers.get("x-crm-secret") !== secret) {
      return json({ error: "unauthorized" }, 401);
    }
    const apiKey = Deno.env.get("ANTHROPIC_API_KEY");
    if (!apiKey) return json({ error: "ANTHROPIC_API_KEY fehlt (Secret setzen)" }, 500);

    const { was, wo } = await req.json().catch(() => ({}));
    if (!was || !wo) return json({ error: "Bitte was und wo angeben" }, 400);

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
- ort und plz sind WICHTIG: ort (Stadt/Gemeinde) IMMER ausfüllen; plz möglichst
  immer mitliefern (aus Impressum/Adresse). Lieber Ort ohne PLZ als gar nichts.
- email: allgemeine Kontakt-/Info-Adresse, wenn auffindbar (z.B. aus dem Impressum).
- geschaeftsfuehrer / betriebsleiter: Namen, wenn auffindbar (Impressum/Handelsregister/LinkedIn).
- jahresmenge: verarbeitete Menge pro Jahr mit Einheit, falls öffentlich (z.B. "ca. 30.000 t/Jahr"), sonst "".
- siebtechnik: welche Siebanlage der Betrieb einsetzt – NUR "Trommelsieb" oder "Sternsieb",
  wenn es klar aus Website/News/Bildern hervorgeht; sonst "" (nicht raten!).
- news: ein relevanter aktueller Punkt mit Jahr (z.B. Erweiterung, Investition, neue Anlage), sonst "".
- quelle: kurz, woher die Infos stammen (z.B. Website, Handelsregister, Presseartikel).
- WICHTIG: Unbekannte Felder als leerer String "". Nichts erfinden – lieber leer lassen.
- 6–8 Firmen pro Antwort genügen. Nur echte, im Web auffindbare Betriebe (keine Dubletten).`;

    const base = {
      model: MODEL,
      max_tokens: 9000,
      // Wenige Web-Suchen -> Antwort bleibt unter ~60 s und kommt auch durch strenge
      // Firmen-Proxies durch. Tiefe entsteht durch die mehrfachen Aufrufe der App.
      tools: [{ type: "web_search_20260209", name: "web_search", max_uses: 5 }],
    };

    // Web-Suche kann mehrere Runden brauchen -> pause_turn-Schleife
    let messages: unknown[] = [{ role: "user", content: prompt }];
    let data: any = null;
    for (let i = 0; i < 10; i++) {
      const r = await fetch(ANTHROPIC_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({ ...base, messages }),
      });
      if (!r.ok) {
        const t = await r.text();
        return json({ error: "anthropic " + r.status, detail: t.slice(0, 400) }, 502);
      }
      data = await r.json();
      if (data.stop_reason === "pause_turn") {
        messages = [...messages, { role: "assistant", content: data.content }];
        continue;
      }
      break;
    }

    let text = (data?.content || [])
      .filter((b: any) => b.type === "text")
      .map((b: any) => b.text)
      .join("\n")
      .trim();
    // Code-Fences entfernen (```json ... ```)
    text = text.replace(/```json/gi, "").replace(/```/g, "");

    // Robustes Herausziehen des JSON-Arrays von Objekten (ignoriert Quellen-Fußnoten wie [1]).
    function extractLeads(t: string): any[] | null {
      // 1) Array, das mit [ { beginnt
      const m = t.match(/\[\s*\{[\s\S]*\}\s*\]/);
      if (m) { try { const a = JSON.parse(m[0]); if (Array.isArray(a)) return a; } catch (_) { /* weiter */ } }
      // 2) gesamter Text
      try { const a = JSON.parse(t.trim()); if (Array.isArray(a)) return a; } catch (_) { /* weiter */ }
      // 3) abgeschnittenes Array retten: bis zum letzten vollständigen } abschneiden und schließen
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

    const leads = extractLeads(text);
    if (leads === null) {
      // Diagnose mitsenden, damit man im App-/Test-Ergebnis sieht, was los war.
      return json({
        leads: [],
        debug: {
          stop_reason: data?.stop_reason || null,
          text_len: text.length,
          truncated: data?.stop_reason === "max_tokens",
          sample: text.slice(0, 500),
        },
      });
    }
    return json({ leads });
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500);
  }
});
