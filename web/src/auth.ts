import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  callbacks: {
    async signIn({ profile }) {
      return (
        profile?.email === "joramkirubi100@gmail.com" &&
        profile?.email_verified === true
      );
    },
  },
});
