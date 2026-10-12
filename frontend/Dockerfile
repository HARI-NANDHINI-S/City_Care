# ==============================================================================
# CivicVision AI — Frontend Containerfile
# Multi-stage build: build static bundle with Node.js, serve with Nginx Alpine
# ==============================================================================

# Stage 1: Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency specifications first for optimal layer caching
COPY frontend/package*.json ./

RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build production distribution bundle
RUN npm run build

# Stage 2: Production serve stage
FROM nginx:alpine

# Copy built distribution from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with reverse proxy for /api and /uploads
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
