import { auth } from "@/auth";
import { hasGoogleToken, removeGoogleToken } from "@/google-store";

export const runtime = "nodejs";
const USER = "joramkirubi100@gmail.com";

export async function GET() {
  const session = await auth();
  if (session?.user?.email !== USER) return Response.json({ error: "Unauthorized" }, { status: 401 });
  try {
    return Response.json({ connected: await hasGoogleToken(USER) }, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ error: "Google storage unavailable" }, { status: 503 });
  }
}

export async function DELETE(request: Request) {
  const session = await auth();
  if (session?.user?.email !== USER) return Response.json({ error: "Unauthorized" }, { status: 401 });
  if (request.headers.get("origin") !== new URL(request.url).origin) {
    return Response.json({ error: "Invalid origin" }, { status: 403 });
  }
  try {
    await removeGoogleToken(USER);
    return Response.json({ connected: false });
  } catch {
    return Response.json({ error: "Google storage unavailable" }, { status: 503 });
  }
}
