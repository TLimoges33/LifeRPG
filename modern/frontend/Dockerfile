FROM node:20-alpine as build
WORKDIR /app
COPY modern/frontend/package.json /app/package.json
COPY modern/frontend/package-lock.json /app/package-lock.json
RUN npm ci
COPY modern/frontend /app
RUN npm run build

FROM node:20-alpine

# Create non-root user for security
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001 -G appuser

WORKDIR /app

COPY --from=build --chown=appuser:appuser /app/dist /app/dist

# Switch to non-root user
USER appuser

RUN npm i -g serve
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
