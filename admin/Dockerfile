# Admin image — AWS ECR Public only (ADR-004, no Docker Hub)
FROM public.ecr.aws/docker/library/node:22-alpine AS build
WORKDIR /app

COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM public.ecr.aws/docker/library/node:22-alpine
WORKDIR /app
ENV HOST=0.0.0.0 PORT=3000

COPY --from=build /app/build ./build
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./

EXPOSE 3000
CMD ["node", "build"]
