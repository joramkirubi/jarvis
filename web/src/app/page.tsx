import { auth, signIn, signOut } from "@/auth";
import VoiceControls from "./voice-controls";

export default async function Home() {
  const session = await auth();
  const signedIn = session?.user?.email === "joramkirubi100@gmail.com";

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-6 text-center text-white">
      <div className="mb-6 rounded-full border border-cyan-400/40 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-300">
        JARVIS
      </div>

      <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
        At your service, Joram.
      </h1>

      {signedIn ? (
        <>
          <p className="mt-5 text-slate-400">
            Signed in as {session.user?.email}
          </p>
          <VoiceControls />
          <form
            action={async () => {
              "use server";
              await signOut();
            }}
          >
            <button className="mt-8 rounded-full border border-slate-600 px-6 py-3">
              Sign out
            </button>
          </form>
        </>
      ) : (
        <>
          <p className="mt-5 max-w-md text-slate-400">
            Sign in to access your private assistant.
          </p>
          <form
            action={async () => {
              "use server";
              await signIn("google");
            }}
          >
            <button className="mt-10 rounded-full bg-cyan-400 px-8 py-4 font-semibold text-slate-950">
              Sign in with Google
            </button>
          </form>
        </>
      )}
    </main>
  );
}
