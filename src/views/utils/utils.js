import * as d3 from "d3";
import axios from "axios";

// 解析 CSV 文件
export function decode_CSV(csv_path) {
  return new Promise((resolve, reject) => {
    d3.csv(csv_path)
      .then((data) => {
        resolve(data);
      })
      .catch((error) => {
        reject(new Error(`读取 CSV 文件时出错: ${error.message}`));
      });
  });
}

/**
 * 检查指定文件夹是否存在，并是否包含 .tif 文件
 * @returns {Promise<boolean>} - 返回文件夹是否存在（或是否有 .tif 文件）
 */
export async function checkFolderExists(folderUrl) {
  try {
    const response = await axios.get(folderUrl);
    console.log("response", response);

    // 根据返回的数据格式进行判定
    if (response.data.files) {
      return true; // 如果文件夹中有 .tif 文件
    } else if (response.data.error || response.data.message) {
      return false; // 如果发生错误或没有找到文件
    }
  } catch (error) {
    console.error("检查文件夹是否存在时出错:", error);
    return false; // 出现错误时认为文件夹不存在
  }
}
