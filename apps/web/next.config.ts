import type { NextConfig } from 'next';
const config: NextConfig = {
  distDir: '.build',
  devIndicators: false,
  poweredByHeader: false,
  async headers() { return [{ source: '/:path*', headers: [
    { key: 'X-Content-Type-Options', value: 'nosniff' },
    { key: 'Referrer-Policy', value: 'same-origin' },
    { key: 'X-Frame-Options', value: 'DENY' },
    { key: 'Permissions-Policy', value: 'microphone=(self), camera=(), geolocation=()' },
  ] }]; },
};
export default config;
