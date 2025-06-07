import * as d3 from "d3";
import axios from "axios";
import proj4 from "proj4";

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

/**
 * 检查main.py是否执行完毕
 * @param {string} finishResponseUrl - 要检查的finish.txt路径
 * @param {Number} executeTimeLimit - 程序执行时间限制（秒）
 * @param {Number} checkInterval - 检查间隔（秒）
 * @returns {object} 返回结果对象
 */
export function checkFinishStatus(
  finishResponseUrl,
  executeTimeLimit = 3600,
  checkInterval = 20
) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now(); // 获取开始时间
    const timeLimit = executeTimeLimit * 1000; // 时间限制 (单位：毫秒)

    const intervalId = setInterval(async () => {
      try {
        // 检查是否超时
        if (Date.now() - startTime > timeLimit) {
          clearInterval(intervalId); // 停止定时器
          console.log("时间已到，未找到 finish.txt 文件");
          resolve(false); // 返回失败标志
          return;
        }

        // 尝试获取文件夹中的文件
        const response = await axios.get(finishResponseUrl);

        // 查找是否存在 finish.txt 文件
        const finishFile = response.data.files.find(
          (file) => file === "finish.txt"
        );

        // 如果 finish.txt 文件存在，表示 main.py 执行完成
        if (finishFile) {
          clearInterval(intervalId); // 停止定时器
          console.log("main.py 执行完成，文件夹中存在 finish.txt");
          resolve(true); // 返回执行完成的标志
        }
      } catch (error) {
        console.error("获取文件列表时出错:", error);
      }
    }, checkInterval * 1000); // 每30秒检查一次
  });
}

export async function reprojectGeoTiff(image) {
  try {
    // 3. 自动获取投影信息
    const geoKeys = image.getGeoKeys();

    // 尝试从不同来源获取投影信息
    let sourceProjection;
    if (geoKeys.ProjectedCSTypeGeoKey) {
      // 使用EPSG代码
      sourceProjection = `EPSG:${geoKeys.ProjectedCSTypeGeoKey}`;
    } else if (geoKeys.GeographicTypeGeoKey) {
      // 地理坐标系
      sourceProjection = `EPSG:${geoKeys.GeographicTypeGeoKey}`;
    }

    if (!sourceProjection) {
      console.warn(
        "Could not automatically determine projection, defaulting to WGS84"
      );
      sourceProjection = "EPSG:4326"; // 默认假设为WGS84
    }

    console.log("Detected source projection:", sourceProjection);

    // 4. 获取边界框并重投影
    const bbox = image.getBoundingBox();
    console.log("Original bounding box:", bbox);

    if (!bbox || bbox.length !== 4) {
      throw new Error("Invalid bounding box retrieved from TIFF image.");
    }

    // 目标投影 (WGS84)
    const targetProjection = "EPSG:4326";
    let reprojectedBbox = null;
    if (sourceProjection === targetProjection) {
      reprojectedBbox = bbox;
    } else {
      // 定义proj4投影 (如果尚未定义)
      if (!proj4.defs(sourceProjection)) {
        // 这里可以添加常见投影的定义
        // 例如UTM zones等
        console.warn(
          `Projection ${sourceProjection} not defined in proj4, attempting to use EPSG.io`
        );
        // 在实际应用中，你可能需要预先定义这些投影
      }

      // 重投影四个角点
      const reprojectedCorners = [
        proj4(sourceProjection, targetProjection, [bbox[0], bbox[1]]), // 左下
        proj4(sourceProjection, targetProjection, [bbox[2], bbox[1]]), // 右下
        proj4(sourceProjection, targetProjection, [bbox[2], bbox[3]]), // 右上
        proj4(sourceProjection, targetProjection, [bbox[0], bbox[3]]), // 左上
      ];

      console.log("Reprojected corners (WGS84):", reprojectedCorners);

      // 计算重投影后的边界框
      reprojectedBbox = [
        Math.min(...reprojectedCorners.map((c) => c[0])), // minX
        Math.min(...reprojectedCorners.map((c) => c[1])), // minY
        Math.max(...reprojectedCorners.map((c) => c[0])), // maxX
        Math.max(...reprojectedCorners.map((c) => c[1])), // maxY
      ];
    }

    console.log("Reprojected bounding box (WGS84):", reprojectedBbox);

    // 5. 返回处理结果
    return reprojectedBbox;
  } catch (error) {
    console.error("Error processing GeoTIFF:", error);
    throw error;
  }
}
