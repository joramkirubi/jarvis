import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { saveGoogleToken } from "@/google-store";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  events: {
    async signIn({ account, profile }) {
      if (
        profile?.email === "joramkirubi100@gmail.com" &&
        profile?.email_verified === true &&
        account?.provider === "google" &&
        account.refresh_token
      ) {
        await saveGoogleToken(profile.email, account.refresh_token);
      }
    },
  },
  callbacks: {
    async signIn({ profile }) {
      return (
        profile?.email === "joramkirubi100@gmail.com" &&
        profile?.email_verified === true
      );
    },
  },
});
