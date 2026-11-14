/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',          // static site in ./out — host anywhere (Netlify, Vercel, S3, any web server)
  images: { unoptimized: true },
  reactStrictMode: false,   // drei <Html> + R3F portals do not tolerate dev double-mounting
};
export default nextConfig;
