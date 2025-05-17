import fs from 'fs/promises';  // 使用异步API
import path from 'path';

export const getFilesInDirectory = async (req, res) => {
  const directoryPath = path.join('E:/04_ZhongyanExperiment/Web_test/Zhongyan_WebGIS', 'public');  // 根据需要修改路径

  try {
    const files = await fs.readdir(directoryPath);  // 异步读取文件夹
    // 过滤出 .tif 文件
    const tifFiles = files.filter(file => file.endsWith('.tif'));
    res.json({ files: tifFiles });  // 返回 .tif 文件
  } catch (err) {
    res.status(500).json({ error: '无法读取文件夹' });
  }
};
