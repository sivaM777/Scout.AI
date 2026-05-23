FROM node:22-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-pip \
  && rm -rf /var/lib/apt/lists/*

COPY package.json tsconfig.base.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY services/api-gateway/package.json services/api-gateway/package.json
COPY apps/mobile/package.json apps/mobile/package.json

RUN npm install --workspace @scout/shared --workspace @scout/api-gateway

COPY packages/shared packages/shared
COPY services/api-gateway services/api-gateway

RUN npm run build --workspace @scout/shared && npm run build --workspace @scout/api-gateway

COPY services/ai-engine/requirements.txt services/ai-engine/requirements.txt
RUN pip3 install --no-cache-dir -r services/ai-engine/requirements.txt

COPY services/ai-engine/app services/ai-engine/app

CMD ["bash", "/app/services/api-gateway/scripts/start-render-free.sh"]
