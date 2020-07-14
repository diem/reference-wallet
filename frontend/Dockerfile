FROM node:12.16.2-alpine3.11

WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH
RUN npm install -g react-scripts --silent

COPY package.json yarn.lock /app/
RUN yarn install

COPY . /app

RUN CI=true yarn test
RUN yarn build

CMD yarn start
