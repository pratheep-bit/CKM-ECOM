/** @type {import('next').NextConfig} */
const nextConfig = {
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: '**',
            },
        ],
    },
    // Enable static exports for Vercel
    output: 'standalone',
};

module.exports = nextConfig;
