FROM node:20-slim AS builder

WORKDIR /app

COPY .yarn /app/.yarn

COPY .yarnrc.yml package.json yarn.lock /app/

RUN yarn install --immutable

COPY ./ /app/

RUN yarn build

FROM nginx:1.29

COPY --from=builder /app/dist/ /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf
