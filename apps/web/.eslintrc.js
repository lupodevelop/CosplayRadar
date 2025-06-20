const { createRequire } = require('module');
const require = createRequire(import.meta.url);

/** @type {import('next').NextConfig} */
const nextConfig = {
  extends: ['next/core-web-vitals', '../../packages/config/eslint.js'],
}

module.exports = nextConfig
