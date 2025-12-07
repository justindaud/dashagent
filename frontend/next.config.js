/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backendUrl = process.env.BACKEND_PROXY_URL || "http://localhost:8000";

    return [
      {
        source: "/api/profile",
        destination: `${backendUrl}/api/profile/`,
      },
      {
        source: "/api/profile/",
        destination: `${backendUrl}/api/profile/`,
      },

      {
        source: "/api/users",
        destination: `${backendUrl}/api/users/`,
      },
      {
        source: "/api/users/",
        destination: `${backendUrl}/api/users/`,
      },

      {
        source: "/api/users/:path*",
        destination: `${backendUrl}/api/users/:path*`,
      },

      {
        source: "/api/sessions",
        destination: `${backendUrl}/api/sessions/`,
      },
      {
        source: "/api/sessions/",
        destination: `${backendUrl}/api/sessions/`,
      },
      {
        source: "/api/sessions/:path*",
        destination: `${backendUrl}/api/sessions/:path*`,
      },

      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
