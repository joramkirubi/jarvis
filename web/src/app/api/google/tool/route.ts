import { auth } from "@/auth";
import { googleRequest } from "@/google-api";

export const runtime = "nodejs";
const USER = "joramkirubi100@gmail.com";

type Input = { action?: unknown; query?: unknown; to?: unknown; subject?: unknown;
  body?: unknown; title?: unknown; start?: unknown; end?: unknown; approved?: unknown };

export async function POST(request: Request) {
  const session = await auth();
  if (session?.user?.email !== USER) return Response.json({ error: "Unauthorized" }, { status: 401 });
  if (request.headers.get("origin") !== new URL(request.url).origin) {
    return Response.json({ error: "Invalid origin" }, { status: 403 });
  }
  let input: Input;
  try {
    if (Number(request.headers.get("content-length") || 0) > 10000) throw new Error();
    input = await request.json();
    if (!input || typeof input !== "object" || Array.isArray(input)) throw new Error();
  } catch {
    return Response.json({ error: "Invalid request" }, { status: 400 });
  }

  try {
    if (input.action === "gmail_recent" || input.action === "gmail_search") {
      if (input.query !== undefined && (typeof input.query !== "string" || input.query.length > 180)) {
        return Response.json({ error: "Invalid search" }, { status: 400 });
      }
      const query = typeof input.query === "string" ? input.query : "";
      const params = new URLSearchParams({ maxResults: "5", q: query });
      const list = await googleRequest(USER, `/gmail/v1/users/me/messages?${params}`) as { messages?: {id: string}[] };
      const messages = await Promise.all((list.messages || []).slice(0, 5).map(async ({ id }) => {
        const msg = await googleRequest(USER, `/gmail/v1/users/me/messages/${encodeURIComponent(id)}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date`) as {
          snippet?: string; payload?: { headers?: { name: string; value: string }[] }; id?: string;
        };
        const header = (name: string) => msg.payload?.headers?.find(h => h.name.toLowerCase() === name)?.value || "";
        return { id: msg.id, from: header("from"), subject: header("subject"), date: header("date"), snippet: msg.snippet };
      }));
      return Response.json({ ok: true, messages }, { headers: { "Cache-Control": "no-store" } });
    }
    if (input.action === "calendar_upcoming") {
      const params = new URLSearchParams({ timeMin: new Date().toISOString(), maxResults: "10", singleEvents: "true", orderBy: "startTime" });
      const result = await googleRequest(USER, `/calendar/v3/calendars/primary/events?${params}`) as {
        items?: { summary?: string; start?: unknown; end?: unknown; htmlLink?: string }[];
      };
      return Response.json({ ok: true, events: (result.items || []).map(e => ({ title: e.summary, start: e.start, end: e.end, link: e.htmlLink })) }, { headers: { "Cache-Control": "no-store" } });
    }
    if (input.action === "gmail_send") {
      if (input.approved !== true) return Response.json({ error: "Confirm the email in your browser before sending" }, { status: 403 });
      const { to, subject, body } = input;
      if (typeof to !== "string" || !/^[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+$/.test(to) || to.length > 254 ||
          typeof subject !== "string" || !subject.trim() || subject.length > 200 || /[\r\n]/.test(subject) ||
          typeof body !== "string" || !body.trim() || body.length > 5000) {
        return Response.json({ error: "Invalid email details" }, { status: 400 });
      }
      const raw = Buffer.from(`To: ${to}\r\nSubject: =?UTF-8?B?${Buffer.from(subject).toString("base64")}?=\r\nMIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\n${body}`, "utf8").toString("base64url");
      const result = await googleRequest(USER, "/gmail/v1/users/me/messages/send", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ raw }),
      });
      return Response.json({ ok: true, result });
    }
    if (input.action === "calendar_create") {
      if (input.approved !== true) return Response.json({ error: "Confirm the event in your browser before creating it" }, { status: 403 });
      const { title, start, end } = input;
      if (typeof title !== "string" || !title.trim() || title.length > 200 ||
          typeof start !== "string" || typeof end !== "string" ||
          !/^\d{4}-\d\d-\d\dT\d\d:\d\d.*(?:Z|[+-]\d\d:\d\d)$/.test(start) ||
          !/^\d{4}-\d\d-\d\dT\d\d:\d\d.*(?:Z|[+-]\d\d:\d\d)$/.test(end) ||
          !Number.isFinite(Date.parse(start)) || !Number.isFinite(Date.parse(end)) ||
          Date.parse(start) >= Date.parse(end)) {
        return Response.json({ error: "Invalid event details; use ISO dates with time zones" }, { status: 400 });
      }
      const result = await googleRequest(USER, "/calendar/v3/calendars/primary/events", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary: title, start: { dateTime: start }, end: { dateTime: end } }),
      });
      return Response.json({ ok: true, result });
    }
    return Response.json({ error: "Unknown action" }, { status: 400 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Google unavailable" }, { status: 502 });
  }
}
