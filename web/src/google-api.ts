import "server-only";
import { getGoogleToken } from "@/google-store";

const ROOT = "https://www.googleapis.com";

async function accessToken(email: string): Promise<string> {
  const refreshToken = await getGoogleToken(email);
  if (!refreshToken) throw new Error("Connect Google in the dashboard first");
  if (!process.env.AUTH_GOOGLE_ID || !process.env.AUTH_GOOGLE_SECRET) {
    throw new Error("Google OAuth is not configured");
  }
  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: process.env.AUTH_GOOGLE_ID,
      client_secret: process.env.AUTH_GOOGLE_SECRET,
      refresh_token: refreshToken,
      grant_type: "refresh_token",
    }),
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(10000),
  });
  if (!response.ok) throw new Error("Google connection expired; reconnect Google");
  const data: unknown = await response.json();
  if (!data || typeof data !== "object" || !("access_token" in data) ||
      typeof data.access_token !== "string") throw new Error("Google token response invalid");
  return data.access_token;
}

export async function googleRequest(email: string, path: string, init?: RequestInit) {
  const token = await accessToken(email);
  const response = await fetch(ROOT + path, {
    ...init,
    headers: { Authorization: `Bearer ${token}`, ...init?.headers },
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(12000),
  });
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error("Google access denied; check permissions and reconnect Google");
    }
    throw new Error(`Google request failed (${response.status})`);
  }
  return response.json();
}
