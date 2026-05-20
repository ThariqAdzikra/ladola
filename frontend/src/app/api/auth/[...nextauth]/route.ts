import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

function handler() {
  const googleClientId = process.env.GOOGLE_CLIENT_ID;
  const googleClientSecret = process.env.GOOGLE_CLIENT_SECRET;

  if (!googleClientId || !googleClientSecret) {
    throw new Error(
      "Missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET. Set them in your environment (Cloud Run service variables / .env.local).",
    );
  }

  return NextAuth({
    providers: [
      GoogleProvider({
        clientId: googleClientId,
        clientSecret: googleClientSecret,
      }),
    ],
    pages: {
      signIn: "/",
    },
    callbacks: {
      async session({ session }) {
        if (session.user) {
          // Send a request to the backend to ensure the user exists in Neon DB
          try {
            const res = await fetch(`${process.env.BACKEND_API_URL || "http://127.0.0.1:8000"}/api/users/sync`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                email: session.user.email,
                name: session.user.name,
                avatar_url: session.user.image,
              }),
            });
            const data = await res.json() as { id?: string };
            if (data && data.id) {
              (session.user as { id?: string }).id = data.id;
            }
          } catch (e) {
            console.error("Failed to sync user with backend:", e);
          }
        }
        return session;
      },
    },
  });
}

export async function GET(request: Request, context: any) {
  return handler()(request, context);
}

export async function POST(request: Request, context: any) {
  return handler()(request, context);
}
