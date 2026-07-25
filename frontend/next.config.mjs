/** @type {import('next').NextConfig} */
const apiUpstream = process.env.API_UPSTREAM ?? "http://localhost:8000";

// Next.js rewrite proxy defaults to 30s (see next/dist/server/lib/router-utils/proxy-request.js).
// AI Candidate Compare cold OpenAI calls are typically ~20s and can spike higher; align with
// the shared LLM timeout headroom so the proxy does not abort with ECONNRESET/socket hang up.
const llmProxyTimeoutMs = Number(process.env.API_PROXY_TIMEOUT_MS ?? 90_000);

const nextConfig = {
  experimental: {
    proxyTimeout: Number.isFinite(llmProxyTimeoutMs) && llmProxyTimeoutMs > 0
      ? llmProxyTimeoutMs
      : 90_000
  },
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
