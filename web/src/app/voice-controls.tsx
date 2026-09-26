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
        jarvis_google: () => JSON.stringify({
          ok: false,
          error: "Google tools are not connected to the website yet.",
        }),
      }}
    >
      <Controls />
    </ConversationProvider>
  );
}
