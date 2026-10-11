import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // The repo root has its own package-lock.json (for the dev launcher), which makes Next
  // treat the whole repo as the project and watch everything in it, including the multi-GB
  // models/ folder. Pin the root to this folder.
  turbopack: {
    root: path.resolve(__dirname),
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'i.ytimg.com',
        port: '',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;
