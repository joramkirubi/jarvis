import "server-only";
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import { neon } from "@neondatabase/serverless";

function encryptionKey(): Buffer {
  const secret = process.env.GOOGLE_TOKEN_ENCRYPTION_KEY;
  if (!secret) throw new Error("GOOGLE_TOKEN_ENCRYPTION_KEY is missing");
  const key = Buffer.from(secret, "base64url");
  if (key.length !== 32) throw new Error("GOOGLE_TOKEN_ENCRYPTION_KEY must be 32 bytes");
  return key;
}

function db() {
  if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is missing");
  return neon(process.env.DATABASE_URL);
}

async function table() {
  await db()`CREATE TABLE IF NOT EXISTS jarvis_google_tokens (
    email text PRIMARY KEY,
    encrypted_refresh_token text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
  )`;
}

function encrypt(value: string): string {
  const nonce = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", encryptionKey(), nonce);
  const data = Buffer.concat([cipher.update(value, "utf8"), cipher.final()]);
  return Buffer.concat([nonce, cipher.getAuthTag(), data]).toString("base64url");
}

function decrypt(value: string): string {
  const data = Buffer.from(value, "base64url");
  if (data.length < 29) throw new Error("Invalid stored token");
  const decipher = createDecipheriv("aes-256-gcm", encryptionKey(), data.subarray(0, 12));
  decipher.setAuthTag(data.subarray(12, 28));
  return Buffer.concat([decipher.update(data.subarray(28)), decipher.final()]).toString("utf8");
}

export async function saveGoogleToken(email: string, token: string) {
  await table();
  await db()`INSERT INTO jarvis_google_tokens (email, encrypted_refresh_token)
    VALUES (${email}, ${encrypt(token)})
    ON CONFLICT (email) DO UPDATE SET encrypted_refresh_token = EXCLUDED.encrypted_refresh_token,
    updated_at = now()`;
}

export async function getGoogleToken(email: string): Promise<string | null> {
  await table();
  const rows = await db()`SELECT encrypted_refresh_token FROM jarvis_google_tokens WHERE email = ${email}`;
  return rows.length ? decrypt(String(rows[0].encrypted_refresh_token)) : null;
}

export async function hasGoogleToken(email: string): Promise<boolean> {
  await table();
  const rows = await db()`SELECT 1 FROM jarvis_google_tokens WHERE email = ${email}`;
  return rows.length > 0;
}

export async function removeGoogleToken(email: string) {
  await table();
  await db()`DELETE FROM jarvis_google_tokens WHERE email = ${email}`;
}
