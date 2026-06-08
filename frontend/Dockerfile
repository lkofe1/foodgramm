# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build

RUN npm install -g http-server

CMD cp -r build/. /app/result_build/ && http-server /app/result_build -p 3000