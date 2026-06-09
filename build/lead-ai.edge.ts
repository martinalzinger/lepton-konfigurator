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

Suche im Web nach REALEN Firmen, die zu "${was}" in der Region "${wo}" passen.
Antworte AUSSCHLIESSLICH mit einem JSON-Array (kein Fließtext, kein Markdown, keine \`\`\`).
Jedes Element exakt so:
{"firma":"","strasse":"","plz":"","ort":"","land":"DE","web":"","tel":"","quelle":""}
- land als Ländercode (DE/AT/CH/...).
- Unbekannte Felder als leerer String "".
- quelle = kurz, woher die Info stammt (z.B. Website, Branchenverzeichnis).
- Höchstens 25 Firmen. Nur echte, im Web auffindbare Betriebe – nichts erfinden.`;

    const base = {
      model: MODEL,
      max_tokens: 8000,
      tools: [{ type: "web_search_20260209", name: "web_search" }],
    };

    // Web-Suche kann mehrere Runden brauchen -> pause_turn-Schleife
    let messages: unknown[] = [{ role: "user", content: prompt }];
    let data: any = null;
    for (let i = 0; i < 6; i++) {
      const r = await fetch("https://api.anthropic.com/v1/messages", {
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

    const text = (data?.content || [])
      .filter((b: any) => b.type === "text")
      .map((b: any) => b.text)
      .join("\n")
      .trim();

    let leads: unknown[] = [];
    try {
      const m = text.match(/\[[\s\S]*\]/);
      const parsed = JSON.parse(m ? m[0] : text);
      if (Array.isArray(parsed)) leads = parsed;
    } catch (_) {
      leads = [];
    }
    return json({ leads });
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500);
  }
});
