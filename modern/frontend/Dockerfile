FROM node:20-alpine as build
WORKDIR /app
COPY modern/frontend/package.json /app/package.json
COPY modern/frontend/package-lock.json /app/package-lock.json
RUN npm ci
COPY modern/frontend /app
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist /app/dist
RUN npm i -g serve
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
