FROM node:22-bookworm

WORKDIR /app

# Install Playwright dependencies
RUN npx playwright install-deps chromium

COPY package*.json ./
COPY prisma ./prisma/

RUN npm install
RUN npx playwright install chromium

COPY . .

RUN npx prisma generate

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start:prod"]
