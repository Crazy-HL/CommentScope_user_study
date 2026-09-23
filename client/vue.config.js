const { defineConfig } = require("@vue/cli-service");

module.exports = defineConfig({
  publicPath: '/comment_scope/',
  transpileDependencies: true,
  devServer: {
    proxy: {
      "/api": {
        target: process.env.EXPERIMENT_API_TARGET || "http://127.0.0.1:8888",
        changeOrigin: true
      }
    }
  }
});
