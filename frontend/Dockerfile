# ==============================================
# Calculadora de Consignados - Frontend Dockerfile
# ==============================================
# Multi-stage build para otimizar tamanho da imagem

# ==============================================
# Stage 1: Dependencies
# ==============================================
FROM node:20-alpine AS deps

# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copiar arquivos de dependências
COPY package.json package-lock.json* ./

# Instalar dependências
RUN npm ci

# ==============================================
# Stage 2: Builder
# ==============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar dependências do stage anterior
COPY --from=deps /app/node_modules ./node_modules

# Copiar código fonte
COPY . .

# Configurar variáveis de ambiente para build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build da aplicação
RUN npm run build

# ==============================================
# Stage 3: Development
# ==============================================
FROM node:20-alpine AS development

WORKDIR /app

# Copiar package.json
COPY package.json package-lock.json* ./

# Instalar todas as dependências (incluindo dev)
RUN npm ci

# Copiar código fonte
COPY . .

# Expor porta
EXPOSE 3000

# Configurar variáveis de ambiente
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Comando padrão (desenvolvimento com hot reload)
CMD ["npm", "run", "dev"]

# ==============================================
# Stage 4: Production Runner
# ==============================================
FROM node:20-alpine AS production

WORKDIR /app

# Criar usuário não-root
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copiar arquivos necessários do builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Mudar para usuário não-root
USER nextjs

# Expor porta
EXPOSE 3000

# Configurar variáveis de ambiente
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Comando padrão
CMD ["node", "server.js"]
