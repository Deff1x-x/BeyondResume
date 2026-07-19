/** @type {import('next').NextConfig} */
const apiUpstream = process.env.API_UPSTREAM ?? "http://localhost:8000";

const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiUpstream.replace(/\/$/, "")}/api/v1/:path*`
      }
    ];
  }
};

export default nextConfig;
