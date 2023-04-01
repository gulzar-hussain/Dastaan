/*
 * Copyright 2021 Google LLC

 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at

 *  https://www.apache.org/licenses/LICENSE-2.0

 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

const path = require("path");
const webpack = require("webpack");
const WebpackShellPluginNext = require("webpack-shell-plugin-next");
const fs = require("fs");
var nodeModules = {};
const Dotenv = require("dotenv-webpack");

fs.readdirSync(path.resolve(__dirname, "node_modules"))
  .filter((x) => [".bin"].indexOf(x) === -1)
  .forEach((mod) => {
    nodeModules[mod] = `commonjs ${mod}`;
  });

const webCONFIG = {
  name: "browser",
  mode: "development",

  entry: {
    app: "./src/app.js",
  },
  devServer: {
    static: {
      directory: path.join(__dirname, "src"),
    },
  },
};

const nodeCONFIG = {
  name: "server",
  mode: "development",
  target: "node",
  entry: {
    server: "./src/server/index.js",
  },
  output: {
    path: path.resolve(__dirname, "build"),
    filename: "[name].bundle.js",
  },
  externals: [nodeModules],
  module: {
    rules: [
      {
        test: /\.js$/,
        use: [
          // 'imports?document=this',

          // 'react-hot',
          "babel-loader",
          //,'jsx-loader'
        ],
      },
      { test: /\.json$/, use: "json-loader" },
    ],
  },
  plugins: [
    new WebpackShellPluginNext({
      onBuildStart: {
        scripts: ["npm run clean:dev && npm run clean:prod"],
        blocking: true,
        parallel: false,
      },
      onBuildEnd: {
        scripts: ["npm run dev"],
        blocking: false,
        parallel: true,
      },
    }),
    new Dotenv(),
    new webpack.DefinePlugin({
      "process.env": JSON.stringify(process.env),
    }),
  ],
  resolve: {
    extensions: [".js"],
    fallback: {
      fs: false,
      tls: false,
      querystring: require.resolve("querystring-es3"),
      events: require.resolve("events"),
      net: false,
      url: require.resolve("url"),
      path: require.resolve("path-browserify"),
      zlib: require.resolve("browserify-zlib"),
      buffer: require.resolve("buffer"),
      http: require.resolve("stream-http"),
      https: require.resolve("https-browserify"),
      stream: require.resolve("stream-browserify"),
      assert: require.resolve("assert"),
      crypto: require.resolve("crypto-browserify"),
      async_hooks: false,
    },
  },
};

// This line enables bundling against src in this repo rather than installed module
module.exports = [webCONFIG, nodeCONFIG];
