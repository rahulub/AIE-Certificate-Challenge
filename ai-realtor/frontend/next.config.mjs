import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendNodeModules = path.resolve(__dirname, 'node_modules');

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      tailwindcss: path.join(frontendNodeModules, 'tailwindcss'),
      'tw-animate-css': path.join(frontendNodeModules, 'tw-animate-css'),
      'lucide-react': path.join(frontendNodeModules, 'lucide-react'),
    };
    return config;
  },
  turbopack: {
    resolveAlias: {
      tailwindcss: './node_modules/tailwindcss',
      'tw-animate-css': './node_modules/tw-animate-css',
      'lucide-react': './node_modules/lucide-react',
    },
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      { source: "/api/ingest", destination: "http://localhost:8000/api/ingest" },
    ]
  },
}

export default nextConfig
