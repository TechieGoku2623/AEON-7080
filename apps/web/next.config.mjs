/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const api = process.env.AEON_API_ORIGIN || "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
