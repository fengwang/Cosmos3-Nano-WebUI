# syntax=docker/dockerfile:1
# WebUI local-build image (MIG-S6). Multi-stage: build the Next.js standalone bundle,
# then ship a slim runner. Talks only to the API service at http://api:8000 (BFF proxy).
# Build from repo root:  docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .

FROM node:22-slim AS build
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.3.0 --activate
# Manifests first for layer caching; pnpm-workspace.yaml carries the allowBuilds policy.
COPY webui/package.json webui/pnpm-lock.yaml webui/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY webui/ ./
# Uses the committed lib/api/schema.d.ts (no gen:api at build). output:"standalone".
RUN pnpm build

FROM node:22-slim AS run
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000
WORKDIR /app
# Standalone server + static assets + public (urdf assets). No source, no node_modules copy.
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
