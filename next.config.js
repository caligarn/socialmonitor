/** @type {import('next').NextConfig} */
const nextConfig = {
  // In local dev, proxy /api/* to the FastAPI server.
  // On Vercel this is handled by vercel.json rewrites, so the proxy is skipped.
  async rewrites() {
    if (process.env.VERCEL) return [];
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
