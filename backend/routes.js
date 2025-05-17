// backend/routes.js

import express from 'express';
import { getFilesInDirectory } from './fileController.js';

const router = express.Router();

// 定义 API 路由
router.get('/files', getFilesInDirectory);

export default router;
