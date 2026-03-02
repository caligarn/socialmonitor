/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        // In dev, proxy to the local FastAPI server
        destination:
          process.env.API_URL
            ? `${process.env.API_URL}/api/:path*`
            : "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
