import express from "express";
import cors from "cors";
import { spawn } from "child_process"; // 使用 spawn 异步执行 Python 脚本
import fs from "fs";
import path from "path";

const app = express();
app.use(cors());

const TIF_FOLDER = "../public/01_TaiWan_Port/Gaoxiong_Port/02_Output";

const MAIN_PY_PATH = "./port_code/main.py";

const SK10_OUTPUT_PATH = "../public/sk10_platform/output";
const TIF_FOLDER_SK10_S1 = "../public/sk10_platform/output/predict";
const TIF_FOLDER_SK10_GAOFEN = "../public/sk10_platform/gaofen";
const OFFSHORE_PLATFORM_MAIN_PY_PATH = "./predict_platform/all_in_one.py";
// 任务进度存储，任务ID -> 进度
let taskProgress = {};

// 检查文件夹中是否存在 .tif 文件
app.get("/api/check-folder", (req, res) => {
  try {
    if (!fs.existsSync(TIF_FOLDER)) {
      return res.status(500).json({ error: "文件夹不存在" });
    }

    let files = fs.readdirSync(TIF_FOLDER).filter((f) => f.endsWith(".tif"));

    if (files.length > 0) {
      return res.json({ files }); // 返回文件列表
    } else {
      return res.status(404).json({ message: "文件夹中未找到 .tif 文件" });
    }
  } catch (err) {
    console.error("Error checking files:", err);
    res.status(500).json({ error: "发生未知错误", details: err.message });
  }
});

// 检查文件夹中是否存在 .tif 文件
app.get("/api/check-folder_sk10_sentinel-1", (req, res) => {
  try {
    if (!fs.existsSync(TIF_FOLDER_SK10_S1)) {
      return res.status(500).json({ error: "文件夹不存在" });
    }

    let files = fs
      .readdirSync(TIF_FOLDER_SK10_S1)
      .filter((f) => f.endsWith(".tif"));

    if (files.length > 0) {
      return res.json({ files }); // 返回文件列表
    } else {
      return res.status(404).json({ message: "文件夹中未找到 .tif 文件" });
    }
  } catch (err) {
    console.error("Error checking files:", err);
    res.status(500).json({ error: "发生未知错误", details: err.message });
  }
});

// 获取 .tif 文件列表，只返回文件名
app.get("/api/files_sk10_sentinel-1", (req, res) => {
  try {
    if (!fs.existsSync(TIF_FOLDER_SK10_S1)) {
      return res.status(500).json({ error: "文件夹不存在" });
    }

    let files = fs
      .readdirSync(TIF_FOLDER_SK10_S1)
      .filter((f) => f.endsWith(".tif"))
      .map((f) => f) // 只返回文件名
      .sort((a, b) => {
        const timeA = fs
          .statSync(path.join(TIF_FOLDER_SK10_S1, a))
          .mtime.getTime();
        const timeB = fs
          .statSync(path.join(TIF_FOLDER_SK10_S1, b))
          .mtime.getTime();
        return timeB - timeA; // 按修改时间降序
      });

    res.json({ files });
  } catch (err) {
    console.error("Error listing files:", err);
    res.status(500).json({ error: "发生未知错误", details: err.message });
  }
});

// 获取 .tif 文件列表，只返回文件名
app.get("/api/files_sk10_gaofen", (req, res) => {
  try {
    if (!fs.existsSync(TIF_FOLDER_SK10_GAOFEN)) {
      return res.status(500).json({ error: "文件夹不存在" });
    }

    let files = fs
      .readdirSync(TIF_FOLDER_SK10_GAOFEN)
      .filter((f) => f.endsWith(".tif"))
      .map((f) => f) // 只返回文件名
      .sort((a, b) => {
        const timeA = fs
          .statSync(path.join(TIF_FOLDER_SK10_GAOFEN, a))
          .mtime.getTime();
        const timeB = fs
          .statSync(path.join(TIF_FOLDER_SK10_GAOFEN, b))
          .mtime.getTime();
        return timeB - timeA; // 按修改时间降序
      });

    res.json({ files });
  } catch (err) {
    console.error("Error listing files:", err);
    res.status(500).json({ error: "发生未知错误", details: err.message });
  }
});

// 运行 main.py，返回任务ID
app.get("/api/run-main_offshore_platform", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [OFFSHORE_PLATFORM_MAIN_PY_PATH]);

  // 捕获 Python 脚本的输出
  process.stdout.on("data", (data) => {
    console.log(`stdout: ${data.toString()}`);
    // 假设 main.py 输出类似：'Progress: 20%'
    const match = data.toString().match(/Progress:\s(\d+)%/);
    if (match) {
      taskProgress[taskId].progress = parseInt(match[1]);
    }
  });

  // 捕获 Python 脚本的错误
  process.stderr.on("data", (data) => {
    console.error(`stderr: ${data.toString()}`);
  });

  // 监听进程结束
  process.on("close", (code) => {
    if (code === 0) {
      taskProgress[taskId].status = "completed"; // 更新任务状态
      console.log(`main.py 执行成功，任务ID: ${taskId}`);
    } else {
      taskProgress[taskId].status = "failed"; // 更新任务状态为失败
      console.error(`main.py 执行失败，任务ID: ${taskId}`);
    }
  });

  res.json({ message: "main.py 执行已启动", taskId });
});

// 获取 .txt 文件列表，只返回文件名
app.get("/api/sk10_platform_finish_txt", (req, res) => {
  try {
    if (!fs.existsSync(SK10_OUTPUT_PATH)) {
      return res.status(500).json({ error: "文件夹不存在" });
    }

    let files = fs
      .readdirSync(SK10_OUTPUT_PATH)
      .filter((f) => f.endsWith(".txt"))
      .map((f) => f) // 只返回文件名
      .sort((a, b) => {
        const timeA = fs
          .statSync(path.join(SK10_OUTPUT_PATH, a))
          .mtime.getTime();
        const timeB = fs
          .statSync(path.join(SK10_OUTPUT_PATH, b))
          .mtime.getTime();
        return timeB - timeA; // 按修改时间降序
      });

    res.json({ files });
  } catch (err) {
    console.error("Error listing files:", err);
    res.status(500).json({ error: "发生未知错误", details: err.message });
  }
});

// 运行 main.py，返回任务ID
app.get("/api/run-main", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH]);

  // 捕获 Python 脚本的输出
  process.stdout.on("data", (data) => {
    console.log(`stdout: ${data.toString()}`);
    // 假设 main.py 输出类似：'Progress: 20%'
    const match = data.toString().match(/Progress:\s(\d+)%/);
    if (match) {
      taskProgress[taskId].progress = parseInt(match[1]);
    }
  });

  // 捕获 Python 脚本的错误
  process.stderr.on("data", (data) => {
    console.error(`stderr: ${data.toString()}`);
  });

  // 监听进程结束
  process.on("close", (code) => {
    if (code === 0) {
      taskProgress[taskId].status = "completed"; // 更新任务状态
      console.log(`main.py 执行成功，任务ID: ${taskId}`);
    } else {
      taskProgress[taskId].status = "failed"; // 更新任务状态为失败
      console.error(`main.py 执行失败，任务ID: ${taskId}`);
    }
  });

  res.json({ message: "main.py 执行已启动", taskId });
});

// 获取任务进度
app.get("/api/task-progress/:taskId", (req, res) => {
  const { taskId } = req.params;
  const progress = taskProgress[taskId];
  if (progress) {
    res.json(progress); // 返回任务进度
  } else {
    res.status(404).json({ error: "任务ID 未找到" });
  }
});

// 获取 .tif 文件列表，只返回文件名
app.get("/api/files", (req, res) => {
  try {
    if (!fs.existsSync(TIF_FOLDER)) {
      return res.status(500).json({ error: "文件夹不存在" });
    }

    let files = fs
      .readdirSync(TIF_FOLDER)
      .filter((f) => f.endsWith(".tif"))
      .map((f) => f) // 只返回文件名
      .sort((a, b) => {
        const timeA = fs.statSync(path.join(TIF_FOLDER, a)).mtime.getTime();
        const timeB = fs.statSync(path.join(TIF_FOLDER, b)).mtime.getTime();
        return timeB - timeA; // 按修改时间降序
      });

    res.json({ files });
  } catch (err) {
    console.error("Error listing files:", err);
    res.status(500).json({ error: "发生未知错误", details: err.message });
  }
});

// 获取 .txt 文件列表，只返回文件名
app.get("/api/files_txt", (req, res) => {
  try {
    if (!fs.existsSync(TIF_FOLDER)) {
      return res.status(500).json({ error: "文件夹不存在" });
    }

    let files = fs
      .readdirSync(TIF_FOLDER)
      .filter((f) => f.endsWith(".txt"))
      .map((f) => f) // 只返回文件名
      .sort((a, b) => {
        const timeA = fs.statSync(path.join(TIF_FOLDER, a)).mtime.getTime();
        const timeB = fs.statSync(path.join(TIF_FOLDER, b)).mtime.getTime();
        return timeB - timeA; // 按修改时间降序
      });

    res.json({ files });
  } catch (err) {
    console.error("Error listing files:", err);
    res.status(500).json({ error: "发生未知错误", details: err.message });
  }
});

app.listen(3017, () => console.log("Server running on port 3017"));
