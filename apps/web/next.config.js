/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@cosplayradar/db', '@cosplayradar/config'],
  experimental: {
    serverComponentsExternalPackages: ['@prisma/client']
  },
  images: {
    domains: ['example.com', 'images.unsplash.com']
  }
};

module.exports = nextConfig;
