FROM node:22-alpine

WORKDIR /app

COPY package.json .

# Install dependencies
RUN npm install

COPY . .

# Expose Vite port
EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
