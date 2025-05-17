// backend/index.js
import express from 'express';
import path from 'path';
import cors from 'cors';
import routes from './routes.js';  // 确保正确导入 routes.js

const app = express();

// 使用 import.meta.url 获取当前模块的路径
const __dirname = path.dirname(new URL(import.meta.url).pathname);

// 启用跨域请求
app.use(cors());

// 继续使用 __dirname 来处理静态文件
app.use(express.static('E:/04_ZhongyanExperiment/Web_test/Zhongyan_WebGIS/public'));

// 使用后端路由
app.use('/api', routes);  // 将路由挂载到 /api 前缀下

// 启动服务，监听 3000 端口
app.listen(3017, () => {
  console.log('Server running on http://localhost:3017');
});
