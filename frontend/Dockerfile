
# Etapa 1: instalar dependencias y compilar
FROM node:22-bookworm-slim AS build

WORKDIR /app

# Copiar primero los archivos de dependencias
COPY package.json package-lock.json ./

# Instalar dependencias
RUN npm ci

# Copiar el resto del codigo
COPY . .

# Compilar React con Vite
RUN npm run build


# Etapa 2: ejecutar la aplicacion
FROM node:22-bookworm-slim

WORKDIR /app

ENV NODE_ENV=production

# Copiar los archivos necesarios
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/vite.config.ts ./

# Puerto del frontend
EXPOSE 3000

# Iniciar la aplicacion compilada
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "3000", "--strictPort"]
