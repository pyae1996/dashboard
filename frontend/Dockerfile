# Stage 1 - Building the app
FROM node:lts-alpine3.18 AS builder

WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install --omit=dev --verbose

# Copy the rest of your frontend application
COPY . ./

# Build the application
RUN npm run build

# Expose port 3001
EXPOSE 3001

# vite command runs the server
CMD ["npm","run","preview"]
