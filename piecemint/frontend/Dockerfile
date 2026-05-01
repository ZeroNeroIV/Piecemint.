# Build static assets — set VITE_API_URL so the browser calls same-origin /api (nginx proxies to api service).
FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=/api
ARG VITE_MARKETPLACE_URL=http://localhost:5174
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MARKETPLACE_URL=$VITE_MARKETPLACE_URL

RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
