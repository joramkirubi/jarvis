"use client";

import {
  ConversationProvider,
  useConversationControls,
  useConversationStatus,
} from "@elevenlabs/react";
import { useState } from "react";

function Controls() {
  const { startSession, endSession } = useConversationControls();
  const { status } = useConversationStatus();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function start() {
    setBusy(true);
    setError("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());

      const response = await fetch("/api/voice/session", {
        method: "POST",
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error("Could not obtain a voice session");
      }

      const data: { signedUrl: string } = await response.json();
      await startSession({ signedUrl: data.signedUrl });
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Voice connection failed",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-10 flex flex-col items-center gap-4">
      <button
        type="button"
        disabled={busy}
        onClick={status === "connected" ? () => void endSession() : () => void start()}
        className="rounded-full bg-cyan-400 px-8 py-4 font-semibold text-slate-950 disabled:opacity-50"
      >
        {busy ? "Connecting…" : status === "connected" ? "End conversation" : "Talk to Jarvis"}
      </button>
      <p className="text-sm text-slate-400">Status: {status}</p>
      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
    </div>
  );
}

export default function VoiceControls() {
  return (
    <ConversationProvider
      clientTools={{
        jarvis_desktop: () => JSON.stringify({
          ok: false,
          error: "Desktop actions are only available in the Windows app.",
        }),
        jarvis_google: async (args: unknown) => {
          if (!args || typeof args !== "object" || !("action" in args)) {
            return JSON.stringify({ ok: false, error: "Google action is missing" });
          }
          const request = { ...args } as Record<string, unknown>;
          if (request.action === "gmail_send") {
            const to = String(request.to || "");
            const subject = String(request.subject || "");
            const body = String(request.body || "");
            request.approved = window.confirm(`Send email to ${to}?\n\nSubject: ${subject}\n\n${body}`);
            if (!request.approved) return JSON.stringify({ ok: false, error: "Email was not approved" });
          } else if (request.action === "calendar_create") {
            request.approved = window.confirm(`Create calendar event?\n\n${String(request.title || "")}\n${String(request.start || "")} to ${String(request.end || "")}`);
            if (!request.approved) return JSON.stringify({ ok: false, error: "Event was not approved" });
          }
          try {
            const response = await fetch("/api/google/tool", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(request),
              cache: "no-store",
            });
            return JSON.stringify(await response.json());
          } catch {
            return JSON.stringify({ ok: false, error: "Could not reach Google tools" });
          }
        },
      }}
    >
      <Controls />
    </ConversationProvider>
  );
}
