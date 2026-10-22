const { DefinePlugin } = require('webpack')

module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },

  chainWebpack: (config) => {
    // 往 index.html 注入构建时间戳（配合 public/index.html 里的 window.__BUILD__）
    // 目的：用户报障时能在控制台确认版本，避免"到底是缓存还是新代码"的来回扯皮。
    config.plugin('html').tap((args) => {
      args[0].templateParameters = {
        ...(args[0].templateParameters || {}),
        BUILD_TIME: new Date().toISOString()
      }
      return args
    })
  }
}
