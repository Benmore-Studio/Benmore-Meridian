import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // ========================================
  // BUILD QUALITY GATES - DO NOT DISABLE
  // ========================================

  // Fail builds on ESLint errors
  eslint: {
    // Set to true to dangerously allow production builds with ESLint errors
    ignoreDuringBuilds: false,
    // Directories to run ESLint on during builds
    dirs: ['src', 'app', 'components', 'lib', 'hooks', 'utils'],
  },

  // Fail builds on TypeScript errors
  typescript: {
    // Set to true to dangerously allow production builds with type errors
    ignoreBuildErrors: false,
  },

  // ========================================
  // REACT & NEXT.JS CONFIGURATION
  // ========================================

  // Enable React Strict Mode for catching bugs
  reactStrictMode: true,

  // ========================================
  // PRODUCTION OPTIMIZATIONS
  // ========================================

  // Remove X-Powered-By header for security
  poweredByHeader: false,

  // Enable gzip compression
  compress: true,

  // ========================================
  // SECURITY HEADERS
  // ========================================

  headers: async () => [
    {
      source: '/:path*',
      headers: [
        // DNS Prefetch Control
        { key: 'X-DNS-Prefetch-Control', value: 'on' },

        // XSS Protection (legacy but still useful)
        { key: 'X-XSS-Protection', value: '1; mode=block' },

        // Prevent clickjacking
        { key: 'X-Frame-Options', value: 'SAMEORIGIN' },

        // Prevent MIME type sniffing
        { key: 'X-Content-Type-Options', value: 'nosniff' },

        // Referrer policy
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },

        // Permissions Policy (formerly Feature-Policy)
        {
          key: 'Permissions-Policy',
          value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
        },
      ],
    },
    // Cache static assets aggressively
    {
      source: '/static/:path*',
      headers: [
        {
          key: 'Cache-Control',
          value: 'public, max-age=31536000, immutable',
        },
      ],
    },
  ],

  // ========================================
  // IMAGE OPTIMIZATION
  // ========================================

  images: {
    // Modern formats for smaller file sizes
    formats: ['image/avif', 'image/webp'],

    // Device sizes for responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],

    // Image sizes for smaller images
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],

    // Minimum cache TTL in seconds (1 minute)
    minimumCacheTTL: 60,

    // Remote patterns for external images (add your CDN/image hosts)
    remotePatterns: [
      // Example:
      // {
      //   protocol: 'https',
      //   hostname: 'images.example.com',
      //   port: '',
      //   pathname: '/**',
      // },
    ],
  },

  // ========================================
  // EXPERIMENTAL FEATURES (Next.js 15+)
  // ========================================

  experimental: {
    // Enable typed routes for Link components
    typedRoutes: true,

    // Optimize package imports (tree shaking)
    optimizePackageImports: ['@tanstack/react-query', 'lodash-es'],
  },

  // ========================================
  // WEBPACK CONFIGURATION
  // ========================================

  webpack: (config, { isServer }) => {
    // Example: Add custom webpack config here if needed

    // Ignore test files in production builds
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
      };
    }

    return config;
  },

  // ========================================
  // OUTPUT CONFIGURATION
  // ========================================

  // Use 'standalone' for Docker deployments
  // output: 'standalone',

  // Custom build directory (default is .next)
  // distDir: '.next',

  // Trailing slash behavior
  trailingSlash: false,

  // Skip middleware URL normalization
  skipMiddlewareUrlNormalize: false,
};

export default nextConfig;
