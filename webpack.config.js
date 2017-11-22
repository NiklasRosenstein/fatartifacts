var path = require('path');
var webpack = require('webpack');

module.exports = {
  entry: './fatartifacts/web/src/app.js',
  output: { path: __dirname + '/fatartifacts/web/static', filename: 'bundle.js' },
  module: {
    loaders: [
      {
        test: /.jsx?$/,
        loader: 'babel-loader',
        exclude: /node_modules/,
        query: {
          presets: ['es2016', 'react']
        }
      }
    ]
  },
};
