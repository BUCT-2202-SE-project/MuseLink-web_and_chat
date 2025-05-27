module.exports = {
  transpileDependencies: [
    'marked',
    'birpc',
    'pinia-plugin-persistedstate'
  ],
  
  devServer: {
    proxy: {
      '/api': {
        // target: 'http://localhost:5000',
        // target: 'http://10.12.112.84:105',
        // target: 'http://10.12.112.166:3200',
        target: 'http://172.20.10.3:3200',
        changeOrigin: true,
        // pathRewrite: { '^/api': '/api' }  // 保留 /api 前缀
      }
    }
  },
  // 临时禁用 ESLint
  lintOnSave: false
}