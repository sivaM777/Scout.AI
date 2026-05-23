FROM node:22-alpine

WORKDIR /app

COPY package.json tsconfig.base.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY services/api-gateway/package.json services/api-gateway/package.json
COPY apps/mobile/package.json apps/mobile/package.json

RUN npm install --workspace @scout/shared --workspace @scout/api-gateway

COPY packages/shared packages/shared
COPY services/api-gateway services/api-gateway

RUN npm run build --workspace @scout/shared && npm run build --workspace @scout/api-gateway

CMD ["node", "services/api-gateway/dist/index.js"]
