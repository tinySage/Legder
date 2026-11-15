/** Static export: Netlify serves plain files. Data is read from public/data at build time. */
const nextConfig = { output: "export", trailingSlash: true, images: { unoptimized: true } };
export default nextConfig;
