import express from "express";
import cors from "cors";
import { spawn } from "child_process"; // 使用 spawn 异步执行 Python 脚本
import fs from "fs";
import path from "path";

const app = express();
app.use(cors());

// 任务进度存储，任务ID -> 进度
let taskProgress = {};

/**
 * 检查文件夹并获取文件列表（同步版本）
 * @param {string} folderPath - 要检查的文件夹路径
 * @param {string} suffix - 要检查的文件后缀
 * @returns {object} 返回结果对象
 */
function getFolderFiles(folderPath, suffix) {
  try {
    // 检查文件夹是否存在
    if (!fs.existsSync(folderPath)) {
      return {
        success: false,
        error: "文件夹不存在",
        statusCode: 500,
      };
    }

    // 读取文件列表
    let filesList = fs
      .readdirSync(folderPath)
      .filter((f) => f.endsWith(suffix));

    if (filesList.length == 0) {
      return {
        success: false,
        error: `文件夹中未找到${suffix}文件`,
        statusCode: 404,
      };
    }

    // 获取文件状态并排序
    const filesWithStats = filesList.map((file) => {
      const stat = fs.statSync(path.join(folderPath, file));
      return {
        name: file,
        mtime: stat.mtime.getTime(),
      };
    });

    let files = filesWithStats
      .sort((a, b) => b.mtime - a.mtime)
      .map((item) => item.name);

    return {
      success: true,
      files,
      count: files.length,
      statusCode: 200,
    };
  } catch (err) {
    console.error("文件操作出错:", err);
    return {
      success: false,
      error: "发生未知错误",
      details: err.message,
      statusCode: 500,
    };
  }
}

// Taiwan_Port
// Gaoxiong_Port
const TIF_FOLDER_Gaoxiong =
  "../public/01_Taiwan_Port/01_Gaoxiong_Port/02_Output";
const MAIN_PY_PATH_Gaoxiong = "./01_Taiwan_Port/01_main_Gaoxiong.py";
const TXT_FOLDER_Gaoxiong = "../public/01_Taiwan_Port/01_Gaoxiong_Port";

// 获取文件夹中的.tif文件
app.get("/api/files_Gaoxiong", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Gaoxiong, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Gaoxiong", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Gaoxiong]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Gaoxiong", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Gaoxiong, ".txt");
  return res.status(result.statusCode).json(result);
});

// Taibei_Port
const TIF_FOLDER_Taibei = "../public/01_Taiwan_Port/02_Taibei_Port/02_Output";
const MAIN_PY_PATH_Taibei = "./01_Taiwan_Port/02_main_Taibei.py";
const TXT_FOLDER_Taibei = "../public/01_Taiwan_Port/02_Taibei_Port";

// 获取文件夹中的.tif文件
app.get("/api/files_Taibei", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Taibei, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Taibei", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Taibei]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Taibei", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Taibei, ".txt");
  return res.status(result.statusCode).json(result);
});

// India_Base
// Durbuk_Base
const TIF_FOLDER_Durbuk = "../public/02_India_Base/01_Durbuk_Base/02_Output";
const MAIN_PY_PATH_Durbuk = "./02_India_Base/01_main_Durbuk.py";
const TXT_FOLDER_Durbuk = "../public/02_India_Base/01_Durbuk_Base";

// 获取文件夹中的.tif文件
app.get("/api/files_Durbuk", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Durbuk, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Durbuk", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Durbuk]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Durbuk", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Durbuk, ".txt");
  return res.status(result.statusCode).json(result);
});

// Chummur_Base
const TIF_FOLDER_Chummur = "../public/02_India_Base/02_Chummur_Base/02_Output";
const MAIN_PY_PATH_Chummur = "./02_India_Base/02_main_Chummur.py";
const TXT_FOLDER_Chummur = "../public/02_India_Base/02_Chummur_Base";

// 获取文件夹中的.tif文件
app.get("/api/files_Chummur", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Chummur, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Chummur", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Chummur]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Chummur", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Chummur, ".txt");
  return res.status(result.statusCode).json(result);
});

// India_Airport
// Bhatinda_Air_Force_Station
const TIF_FOLDER_Bhatinda =
  "../public/03_India_Airport/01_Bhatinda_Air_Force_Station/02_Output";
const MAIN_PY_PATH_Bhatinda =
  "./03_India_Airport/01_main_Bhatinda_Air_Force_Station.py";
const TXT_FOLDER_Bhatinda =
  "../public/03_India_Airport/01_Bhatinda_Air_Force_Station";

// 获取文件夹中的.tif文件
app.get("/api/files_Bhatinda", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Bhatinda, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Bhatinda", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Bhatinda]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Bhatinda", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Bhatinda, ".txt");
  return res.status(result.statusCode).json(result);
});

// Silchar_Airport
const TIF_FOLDER_Silchar =
  "../public/03_India_Airport/02_Silchar_Airport/02_Output";
const MAIN_PY_PATH_Silchar = "./03_India_Airport/02_main_Silchar_Airport.py";
const TXT_FOLDER_Silchar = "../public/03_India_Airport/02_Silchar_Base";

// 获取文件夹中的.tif文件
app.get("/api/files_Silchar", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Silchar, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Silchar", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Silchar]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Silchar", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Silchar, ".txt");
  return res.status(result.statusCode).json(result);
});

// Dehradun_Airport
const TIF_FOLDER_Dehradun =
  "../public/03_India_Airport/03_Dehradun_Airport/02_Output";
const MAIN_PY_PATH_Dehradun = "./03_India_Airport/03_main_Dehradun_Airport.py";
const TXT_FOLDER_Dehradun = "../public/03_India_Airport/03_Dehradun_Airport";

// 获取文件夹中的.tif文件
app.get("/api/files_Dehradun", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Dehradun, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Dehradun", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Dehradun]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Dehradun", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Dehradun, ".txt");
  return res.status(result.statusCode).json(result);
});

// Leh_Airport
const TIF_FOLDER_Leh = "../public/03_India_Airport/04_Leh_Airport/02_Output";
const MAIN_PY_PATH_Leh = "./03_India_Airport/04_main_Leh_Airport.py";
const TXT_FOLDER_Leh = "../public/03_India_Airport/04_Leh_Airport";

// 获取文件夹中的.tif文件
app.get("/api/files_Leh", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Leh, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Leh", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Leh]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Leh", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Leh, ".txt");
  return res.status(result.statusCode).json(result);
});

// Lengpui_Airport
const TIF_FOLDER_Lengpui =
  "../public/03_India_Airport/05_Lengpui_Airport/02_Output";
const MAIN_PY_PATH_Lengpui = "./03_India_Airport/05_main_Lengpui_Airport.py";
const TXT_FOLDER_Lengpui = "../public/03_India_Airport/05_Lengpui_Airport";

// 获取文件夹中的.tif文件
app.get("/api/files_Lengpui", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Lengpui, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Lengpui", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Lengpui]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Lengpui", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Lengpui, ".txt");
  return res.status(result.statusCode).json(result);
});

// Chabua_Air_Force_Station
const TIF_FOLDER_Chabua =
  "../public/03_India_Airport/06_Chabua_Air_Force_Station/02_Output";
const MAIN_PY_PATH_Chabua =
  "./03_India_Airport/06_main_Chabua_Air_Force_Station.py";
const TXT_FOLDER_Chabua =
  "../public/03_India_Airport/06_Chabua_Air_Force_Station";

// 获取文件夹中的.tif文件
app.get("/api/files_Chabua", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Chabua, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Chabua", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Chabua]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Chabua", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Chabua, ".txt");
  return res.status(result.statusCode).json(result);
});

// Shilong_Airport
const TIF_FOLDER_Shilong =
  "../public/03_India_Airport/07_Shilong_Airport/02_Output";
const MAIN_PY_PATH_Shilong = "./03_India_Airport/07_main_Shilong_Airport.py";
const TXT_FOLDER_Shilong = "../public/03_India_Airport/07_Shilong_Airport";

// 获取文件夹中的.tif文件
app.get("/api/files_Shilong", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Shilong, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run_main_Shilong", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [MAIN_PY_PATH_Shilong]);

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

// 获取文件夹中的.txt文件
app.get("/api/files_txt_Shilong", async (req, res) => {
  const result = await getFolderFiles(TXT_FOLDER_Shilong, ".txt");
  return res.status(result.statusCode).json(result);
});

// Pakistan_Lake
// Hassanabad
const TIF_FOLDER_Hassanabad =
  "../public/04_Pakistan_Lake/01_Hassanabad/02_Output";

// 获取文件夹中的.tif文件
app.get("/api/files_Hassanabad", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Hassanabad, ".tif");
  return res.status(result.statusCode).json(result);
});

// India_Airplane
// Thoise
const TIF_FOLDER_Thoise = "../public/05_India_Airplane/01_Thoise/02_Output";

// 获取文件夹中的.tif文件
app.get("/api/files_Thoise", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Thoise, ".tif");
  return res.status(result.statusCode).json(result);
});

// Leh_Airplane
const TIF_FOLDER_Leh_Airplane = "../public/05_India_Airplane/02_Leh/02_Output";

// 获取文件夹中的.tif文件
app.get("/api/files_Leh_Airplane", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Leh_Airplane, ".tif");
  return res.status(result.statusCode).json(result);
});

const Indian_River_Tributary_OUTPUT_PATH = "../public/River_Expand";
const TIF_FOLDER_Indian_River_Tributary = "../public/River_Expand/result";

// 获取文件夹中的.tif文件
app.get("/api/files_indian_river_tributary", async (req, res) => {
  const result = await getFolderFiles(
    TIF_FOLDER_Indian_River_Tributary,
    ".tif"
  );
  return res.status(result.statusCode).json(result);
});

const Xianbinjiao_OUTPUT_PATH = "../public/Ship_Gather/01_Xianbinjiao";
const Nanhuajiao_OUTPUT_PATH = "../public/Ship_Gather/02_Nanhuajiao";
const TIF_FOLDER_Xianbinjiao = "../public/Ship_Gather/01_Xianbinjiao/result";
const TIF_FOLDER_Nanhuajiao = "../public/Ship_Gather/02_Nanhuajiao/result";

// 获取文件夹中的.tif文件
app.get("/api/files_xianbinjiao", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Xianbinjiao, ".tif");
  return res.status(result.statusCode).json(result);
});

// 获取文件夹中的.tif文件
app.get("/api/files_nanhuajiao", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Nanhuajiao, ".tif");
  return res.status(result.statusCode).json(result);
});

const Mandehaixia_OUTPUT_PATH = "../public/Ship_Disperse/";
const TIF_FOLDER_Mandehaixia = "../public/Ship_Disperse//result";

// 获取文件夹中的.tif文件
app.get("/api/files_mandehaixia", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Mandehaixia, ".tif");
  return res.status(result.statusCode).json(result);
});

const Baijiao_OUTPUT_PATH = "../public/Nansha_Island/01_Baijiao/02_Output";
const Bishengjiao_OUTPUT_PATH =
  "../public/Nansha_Island/02_Bishengjiao/02_Output";
const TIF_FOLDER_Baijiao = "../public/Nansha_Island/01_Baijiao/test/merge";
const TIF_FOLDER_Bishengjiao =
  "../public/Nansha_Island/02_Bishengjiao/test/merge";
const Baijiao_MAIN_PY_PATH = "./Nansha_Island/01_main_baijiao.py";
const Bishengjiao_MAIN_PY_PATH = "./Nansha_Island/02_main_bishengjiao.py";

// 获取文件夹中的.tif文件
app.get("/api/files_baijiao", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Baijiao, ".tif");
  return res.status(result.statusCode).json(result);
});

// 获取文件夹中的.tif文件
app.get("/api/files_bishengjiao", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_Bishengjiao, ".tif");
  return res.status(result.statusCode).json(result);
});

// 运行 main.py，返回任务ID
app.get("/api/run-main_baijiao", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [Baijiao_MAIN_PY_PATH]);

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
});

// 运行 main.py，返回任务ID
app.get("/api/run-main_bishengjiao", (req, res) => {
  const taskId = Date.now(); // 生成唯一任务ID
  taskProgress[taskId] = { progress: 0, status: "running" }; // 初始化任务进度为0

  console.log(`Starting main.py with task ID: ${taskId}`);

  const process = spawn("python", [Bishengjiao_MAIN_PY_PATH]);

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

// 获取文件夹中的.txt文件
app.get("/api/baijiao_finish_txt", async (req, res) => {
  const result = await getFolderFiles(Baijiao_OUTPUT_PATH, ".txt");
  return res.status(result.statusCode).json(result);
});

// 获取文件夹中的.txt文件
app.get("/api/bishengjiao_finish_txt", async (req, res) => {
  const result = await getFolderFiles(Bishengjiao_OUTPUT_PATH, ".txt");
  return res.status(result.statusCode).json(result);
});

const SK10_OUTPUT_PATH = "../public/sk10_platform/output";
const TIF_FOLDER_SK10_S1 = "../public/sk10_platform/output/predict";
const TIF_FOLDER_SK10_GAOFEN = "../public/sk10_platform/gaofen";
const OFFSHORE_PLATFORM_MAIN_PY_PATH = "./predict_platform/all_in_one.py";

// 获取文件夹中的.tif文件
app.get("/api/files_sk10_sentinel-1", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_SK10_S1, ".tif");
  return res.status(result.statusCode).json(result);
});

// 获取文件夹中的.tif文件
app.get("/api/files_sk10_gaofen", async (req, res) => {
  const result = await getFolderFiles(TIF_FOLDER_SK10_GAOFEN, ".tif");
  return res.status(result.statusCode).json(result);
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

// 获取文件夹中的.txt文件
app.get("/api/sk10_platform_finish_txt", async (req, res) => {
  const result = await getFolderFiles(SK10_OUTPUT_PATH, ".txt");
  return res.status(result.statusCode).json(result);
});

// all
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

app.listen(3017, () => console.log("Server running on port 3017"));
