import type { NextConfig } from "next";

const backendUrl =
  process.env.BACKEND_API_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "i.pravatar.cc",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/predict",
        destination: `${backendUrl}/predict`,
      },
      {
        source: "/chat",
        destination: `${backendUrl}/chat`,
      },
      {
        source: "/diseases",
        destination: `${backendUrl}/diseases`,
      },
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
      {
        source: "/api/chat-sessions/:path*",
        destination: `${backendUrl}/api/chat-sessions/:path*`,
      },
      {
        source: "/api/users/:path*",
        destination: `${backendUrl}/api/users/:path*`,
      },
    ];
  },
};

export default nextConfig;
