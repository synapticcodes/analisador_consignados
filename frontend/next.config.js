/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Configurações de otimização
  poweredByHeader: false,
  compress: true,

  // Configurações de imagens
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
      {
        protocol: 'http',
        hostname: 'minio',
      },
    ],
  },

  // Turbopack (Next.js 16)
  turbopack: {},

  // Configurações experimentais (Next.js 16)
  experimental: {
    // Habilitar otimizações de cache
    staleTimes: {
      dynamic: 30,
      static: 180,
    },
  },

  // Variáveis de ambiente públicas
  env: {
    NEXT_PUBLIC_APP_NAME: 'Calculadora de Consignados',
    NEXT_PUBLIC_APP_VERSION: '1.0.0',
  },

  // Webpack customization (se necessário)
  webpack: (config, { isServer }) => {
    // Customizações de webpack aqui
    return config
  },
}

module.exports = nextConfig
