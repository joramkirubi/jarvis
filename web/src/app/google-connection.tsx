"use client";

import { useEffect, useState } from "react";

export default function GoogleConnection() {
  const [status, setStatus] = useState("Checking Google connection…");
  const [result, setResult] = useState("");
  useEffect(() => {
    fetch("/api/google/status", { cache: "no-store" })
      .then(async response => {
        if (!response.ok) throw new Error("Connection status unavailable");
        return response.json() as Promise<{ connected: boolean }>;
      })
      .then(data => setStatus(data.connected ? "Gmail and Calendar connected" : "Gmail and Calendar not connected"))
      .catch(() => setStatus("Connection status unavailable"));
  }, []);

  async function preview(action: "gmail_recent" | "calendar_upcoming") {
    setResult("Loading…");
    try {
      const response = await fetch("/api/google/tool", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }), cache: "no-store",
      });
      const data = await response.json();
      setResult(JSON.stringify(data, null, 2));
    } catch {
      setResult("Could not reach Google tools");
    }
  }

  return (
    <section className="mt-8 max-w-lg text-sm text-slate-300">
      <p>{status}</p>
      {status.includes("connected") && !status.includes("not connected") && (
        <div className="mt-3 flex flex-wrap justify-center gap-2">
          <button type="button" onClick={() => void preview("gmail_recent")} className="rounded border border-slate-600 px-3 py-2">Recent email</button>
          <button type="button" onClick={() => void preview("calendar_upcoming")} className="rounded border border-slate-600 px-3 py-2">Upcoming events</button>
          <button type="button" onClick={async () => {
            if (!window.confirm("Disconnect Jarvis from Gmail and Calendar?")) return;
            const response = await fetch("/api/google/status", { method: "DELETE" });
            if (response.ok) { setStatus("Gmail and Calendar not connected"); setResult(""); }
            else setResult("Disconnect failed");
          }} className="rounded border border-red-500 px-3 py-2">Disconnect</button>
        </div>
      )}
      {result && <pre className="mt-3 max-h-52 overflow-auto whitespace-pre-wrap break-all rounded bg-slate-900 p-3 text-left">{result}</pre>}
    </section>
  );
}
