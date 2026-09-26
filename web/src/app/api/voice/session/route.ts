import { auth } from "@/auth";

export const runtime = "nodejs";

export async function POST() {
  const session = await auth();

  if (session?.user?.email !== "joramkirubi100@gmail.com") {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const apiKey = process.env.ELEVENLABS_API_KEY;
  const agentId = process.env.ELEVENLABS_AGENT_ID;

  if (!apiKey || !agentId) {
    return Response.json(
      { error: "Voice service is not configured" },
      { status: 503 },
    );
  }

  try {
    const url = new URL(
      "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url",
    );
    url.searchParams.set("agent_id", agentId);

    const response = await fetch(url, {
      headers: { "xi-api-key": apiKey },
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      return Response.json(
        { error: "Could not start a voice session" },
        { status: 502 },
      );
    }

    const data: unknown = await response.json();

    if (
      !data ||
      typeof data !== "object" ||
      !("signed_url" in data) ||
      typeof data.signed_url !== "string"
    ) {
      return Response.json(
        { error: "Invalid voice service response" },
        { status: 502 },
      );
    }

    return Response.json(
      { signedUrl: data.signed_url },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return Response.json(
      { error: "Voice service unavailable" },
      { status: 502 },
    );
  }
}
