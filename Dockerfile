FROM node:20-bookworm

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3001
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    build-essential \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
RUN npm ci

COPY requirements.txt ./
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

RUN chmod +x ./scripts/build_credibility_bridge.sh \
    && npm run build:bridge \
    && npm run build

EXPOSE 3001

CMD ["npm", "run", "start"]
