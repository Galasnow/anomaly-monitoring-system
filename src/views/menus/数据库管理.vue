<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import AMapLoader from "@amap/amap-jsapi-loader";
import { Amap_security_Code, Amap_key } from "../../../my_package.json";
import axios from "axios";
// import GD from "./GD.json";
// import VueSwitch from "vue-switch";

// 注册组件
// const components = {
//   VueSwitch,
// };

let map = null;
let AMapInstance = null;
let markers = []; // 用来存放所有标记

onMounted(() => {
  window._AMapSecurityConfig = {
    securityJsCode: Amap_security_Code,
  };
  // 加载高德地图
  AMapLoader.load({
    key: Amap_key,
    version: "2.0",
    plugins: ["AMap.Scale", "AMap.GeoJSON"], // 插件列表
  }).then((AMap) => {
    AMapInstance = AMap;
    // 初始化地图
    map = new AMap.Map("container", {
      zoom: 15,
      center: [75.229351, 37.771813], // 默认位置
      viewMode: "3D",
      layers: [new AMap.TileLayer.Satellite(), new AMap.TileLayer.RoadNet()],
    });
  });
});

onUnmounted(() => {
  map?.destroy();
  markers.forEach((marker) => {
    marker.setMap(null); // 移除所有标记
  });
  markers = [];
});

// 响应式数据
const query = ref({
  poiName: "", // POI查询的名称
  roadName: "", // 道路查询的名称
});
const poiResults = ref([]);
const roadResults = ref([]);
const loading = ref(false);
const error = ref(null);
const bridgeResults = ref([]);
const kouanResults = ref([]);
const mergeResults = ref([]);
const towersResults = ref([]);

const clearMarkers = () => {
  markers.forEach((marker) => {
    marker.setMap(null);
  });
  markers = [];
};

// POI查询方法
const handlePOISearch = async () => {
  clearMarkers(); // 清除之前的标记
  poiResults.value = []; // 清除POI查询结果
  roadResults.value = []; // 清除道路查询结果
  loading.value = true;
  error.value = null;

  try {
    const response = await axios.get(
      "http://127.0.0.1:8989/api/v1/db/search_poi",
      {
        params: {
          name: query.value.poiName,
        },
      }
    );

    const pois = response.data;
    const points = pois.map(
      (poi) => new AMapInstance.LngLat(poi.longitude, poi.latitude)
    );
    AMapLoader.load({
      key: Amap_key,
      version: "2.0",
      plugins: ["AMap.Convertor"],
    })
      .then((AMap) => {
        AMap.convertFrom(points, "gps", (status, result) => {
          if (status === "complete") {
            const convertedPois = pois.map((poi, index) => {
              const convertedPoint = result.locations[index];
              return {
                ...poi,
                longitude: convertedPoint.lng,
                latitude: convertedPoint.lat,
              };
            });
            poiResults.value = convertedPois;

            if (poiResults.value.length === 0) {
              error.value = "未找到相关POI";
            } else {
              const data = poiResults.value;
              const type = "POI";
              const iconUrl = "src/assets/db_icons/poi.png";
              data.forEach((item) => {
                const marker = new AMapInstance.Marker({
                  position: new AMapInstance.LngLat(
                    item.longitude,
                    item.latitude
                  ),
                  map: map,
                  title: item.name,
                  label: {
                    offset: new AMapInstance.Pixel(0, -30),
                  },
                  icon: new AMapInstance.Icon({
                    image: iconUrl, // 使用自定义图标URL
                    size: new AMapInstance.Size(45, 45), // 图标大小
                    imageSize: new AMapInstance.Size(45, 45), // 图标显示大小
                    anchor: new AMapInstance.Pixel(16, 32), // 锚点位置，使图标底部对齐地理坐标点
                  }),
                });
                marker.type = type; // 添加类型标识
                markers.push(marker);
              });
            }
          } else {
            error.value = "坐标转换失败";
          }
        });
      })
      .catch((e) => {
        error.value = "坐标转换失败";
        console.error(e);
      });
  } catch (err) {
    error.value = err.response ? err.response.data.detail : "查询失败";
  } finally {
    loading.value = false;
  }
};

// 定位功能，点击某个 POI 后，将地图定位到该 POI
const handleLocate = (longitude, latitude, name) => {
  // 更新地图中心
  map.setCenter([longitude, latitude]);

  // 如果之前有标记，先移除
  clearMarkers();

  // 创建标记
  const marker = new AMapInstance.Marker({
    position: new AMapInstance.LngLat(longitude, latitude),
    map: map,
    animation: "AMAP_ANIMATION_BOUNCE",
    clickable: true,
    draggable: false,
    icon: new AMapInstance.Icon({
      image: "src/assets/db_icons/poi.png", // 替换为你的自定义图标URL
      size: new AMapInstance.Size(42, 42), // 图标大小
      imageSize: new AMapInstance.Size(42, 42), // 图标显示大小
      anchor: new AMapInstance.Pixel(16, 32), // 锚点位置，使图标底部对齐地理坐标点
    }),
    title: name, // 设置标记的提示
    label: {
      offset: new AMapInstance.Pixel(0, -30), // 标签偏移量
    },
  });
  markers.push(marker);
};

const handleLocateRoad = async (road) => {
  clearMarkers(); // 清除之前的标记
  if (
    !road ||
    !road.geojson ||
    !road.geojson.coordinates ||
    road.geojson.coordinates.length === 0
  ) {
    console.error("无效的道路数据");
    return;
  }

  const newPolylines = [];

  for (const part of road.geojson.coordinates) {
    try {
      const convertedPart = await convertCoordinates(part);
      const path = convertedPart.map((coord) => [coord[0], coord[1]]);

      const polyline = new AMapInstance.Polyline({
        path: path,
        strokeColor: "#0056b3",
        strokeOpacity: 0.8,
        strokeWeight: 8,
        zIndex: 50,
        bubble: true,
        strokeStyle: "solid",
        lineJoin: "round",
        lineCap: "round",
        borderWeight: 2,
        borderColor: "#ffffff",
        borderOpacity: 0.8,
      });

      polyline.setMap(map);
      newPolylines.push(polyline);
    } catch (error) {
      console.error("坐标转换错误:", error);
    }
  }

  const firstCoordinates = road.geojson.coordinates[0][0];
  map.setCenter([firstCoordinates[1], firstCoordinates[0]]);
  map.setZoom(15); // 根据实际情况调整缩放级别

  const marker = new AMapInstance.Marker({
    position: [firstCoordinates[1], firstCoordinates[0]],
    map: map,
    title: road.name,
    label: {
      offset: new AMapInstance.Pixel(0, -30),
    },
  });
  markers.push(marker);

  map.setFitView(newPolylines);
};

// 坐标转换函数
const convertCoordinates = (coordinates) => {
  return new Promise((resolve, reject) => {
    AMapLoader.load({
      key: Amap_key,
      version: "2.0",
      plugins: ["AMap.Convertor"],
    })
      .then((AMap) => {
        const points = coordinates.map(
          (coord) => new AMapInstance.LngLat(coord[0], coord[1])
        );
        AMap.convertFrom(points, "gps", (status, result) => {
          if (status === "complete") {
            const convertedPoints = result.locations.map((loc) => [
              loc.lng,
              loc.lat,
            ]);
            resolve(convertedPoints);
          } else {
            reject(new Error("坐标转换失败"));
          }
        });
      })
      .catch((e) => {
        reject(e);
      });
  });
};

// 道路查询方法
const handleRoadSearch = async () => {
  clearMarkers(); // 清除之前的标记
  poiResults.value = []; // 清除POI查询结果
  roadResults.value = []; // 清除道路查询结果
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get(
      "http://127.0.0.1:8989/api/v1/db/search_road",
      {
        params: {
          road_name: query.value.roadName, // 修改为查询道路名称
        },
      }
    );

    roadResults.value = response.data;

    if (roadResults.value.length === 0) {
      error.value = "未找到相关道路";
    } else {
      // 更新地图中心到第一条道路的第一个坐标点
      const firstRoad = roadResults.value[0];
      const firstCoordinates = firstRoad.geojson.coordinates[0][0];

      map.setCenter(firstCoordinates);

      const point = new AMap.LngLat(firstCoordinates[0], firstCoordinates[1]);

      // 使用 AMap.Convertor 进行坐标转换
      AMapLoader.load({
        key: Amap_key, // 替换为您的高德地图 API Key
        version: "2.0",
        plugins: ["AMap.Convertor"],
      })
        .then((AMap) => {
          AMap.convertFrom([point], "gps", (status, result) => {
            if (status === "complete") {
              const convertedPoint = result.locations[0];
              const convertedCoordinates = [
                convertedPoint.lng,
                convertedPoint.lat,
              ];

              // 更新地图中心到转换后的第一个坐标点
              map.setCenter(convertedCoordinates);

              // 添加标记到转换后的第一个坐标点
              const marker = new AMap.Marker({
                position: convertedCoordinates, // 转换后的第一个坐标点
                map: map, // 添加到地图上
                title: firstRoad.name, // 设置标记的提示
              });
              markers.push(marker);
            } else {
              console.error("坐标转换失败");
            }
          });
        })
        .catch((e) => {
          console.error("加载 AMap 失败", e);
        });
    }
  } catch (err) {
    error.value = err.response ? err.response.data.detail : "查询失败";
  } finally {
    loading.value = false;
  }
};

const handleBridgeToggle = async (event) => {
  if (event.target.checked) {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8989/api/v1/db/search_bridge"
      );
      const bridges = response.data;

      // 提取坐标
      const coordinates = bridges.map((bridge) => [
        bridge.longitude,
        bridge.latitude,
      ]);

      // 批量转换坐标
      const convertedCoordinates = await convertCoordinatesBatch(coordinates);

      // 更新桥梁数据
      const convertedBridges = bridges.map((bridge, index) => ({
        ...bridge,
        longitude: convertedCoordinates[index][0],
        latitude: convertedCoordinates[index][1],
      }));

      bridgeResults.value = convertedBridges;
      loadMarkers(
        bridgeResults.value,
        "Bridge",
        "src/assets/db_icons/bridge.png"
      );
      map.setCenter([75.811972, 37.105886]);
      map.setZoom(8);
    } catch (err) {
      console.error("加载 bridge 数据失败:", err);
    }
  } else {
    clearMarkersByType("Bridge");
  }
};

const handleKouanToggle = async (event) => {
  if (event.target.checked) {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8989/api/v1/db/search_kouan"
      );
      const kouans = response.data;

      // 提取坐标
      const coordinates = kouans.map((kouan) => [
        kouan.longitude,
        kouan.latitude,
      ]);

      // 批量转换坐标
      const convertedCoordinates = await convertCoordinatesBatch(coordinates);

      // 更新口岸数据
      const convertedKouans = kouans.map((kouan, index) => ({
        ...kouan,
        longitude: convertedCoordinates[index][0],
        latitude: convertedCoordinates[index][1],
      }));

      kouanResults.value = convertedKouans;
      loadMarkers(kouanResults.value, "Kouan", "src/assets/db_icons/kouan.png");
      map.setCenter([75.811972, 37.105886]);
      map.setZoom(8);
    } catch (err) {
      console.error("加载 kouan 数据失败:", err);
    }
  } else {
    clearMarkersByType("Kouan");
  }
};

const handleMergeToggle = async (event) => {
  if (event.target.checked) {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8989/api/v1/db/search_merge"
      );
      const merges = response.data;

      // 提取坐标
      const coordinates = merges.map((merge) => [
        merge.longitude,
        merge.latitude,
      ]);

      // 批量转换坐标
      const convertedCoordinates = await convertCoordinatesBatch(coordinates);

      // 更新居民点数据
      const convertedMerges = merges.map((merge, index) => ({
        ...merge,
        longitude: convertedCoordinates[index][0],
        latitude: convertedCoordinates[index][1],
      }));

      mergeResults.value = convertedMerges;
      loadMarkers(mergeResults.value, "Merge", "src/assets/db_icons/merge.png");
      map.setCenter([75.811972, 37.105886]);
      map.setZoom(8);
    } catch (err) {
      console.error("加载 merge 数据失败:", err);
    }
  } else {
    clearMarkersByType("Merge");
  }
};

const handleTowersToggle = async (event) => {
  if (event.target.checked) {
    try {
      const response = await axios.get(
        "http://127.0.0.1:8989/api/v1/db/search_towers"
      );
      const towers = response.data;

      // 提取坐标
      const coordinates = towers.map((tower) => [
        tower.longitude,
        tower.latitude,
      ]);

      // 批量转换坐标
      const convertedCoordinates = await convertCoordinatesBatch(coordinates);

      // 更新塔营地数据
      const convertedTowers = towers.map((tower, index) => ({
        ...tower,
        longitude: convertedCoordinates[index][0],
        latitude: convertedCoordinates[index][1],
      }));

      towersResults.value = convertedTowers;
      loadMarkers(
        towersResults.value,
        "Tower",
        "src/assets/db_icons/tower.png"
      );
      map.setCenter([75.811972, 37.105886]);
      map.setZoom(8);
    } catch (err) {
      console.error("加载 towers 数据失败:", err);
    }
  } else {
    clearMarkersByType("Tower");
  }
};

const loadMarkers = (data, type, iconUrl) => {
  data.forEach((item) => {
    const marker = new AMapInstance.Marker({
      position: new AMapInstance.LngLat(item.longitude, item.latitude),
      map: map,
      title: item.name,
      label: {
        offset: new AMapInstance.Pixel(0, -30),
      },
      icon: new AMapInstance.Icon({
        image: iconUrl, // 使用自定义图标URL
        size: new AMapInstance.Size(25, 35), // 图标大小
        imageSize: new AMapInstance.Size(25, 35), // 图标显示大小
        anchor: new AMapInstance.Pixel(16, 32), // 锚点位置，使图标底部对齐地理坐标点
      }),
    });
    marker.type = type; // 添加类型标识
    markers.push(marker);
  });
};

const clearMarkersByType = (type) => {
  markers = markers.filter((marker) => {
    if (marker.type !== type) {
      return true;
    } else {
      marker.setMap(null);
      return false;
    }
  });
};
// 批量坐标转换函数
const convertCoordinatesBatch = (coordinates) => {
  return new Promise((resolve, reject) => {
    AMapLoader.load({
      key: Amap_key,
      version: "2.0",
      plugins: ["AMap.Convertor"],
    })
      .then((AMap) => {
        const points = coordinates.map(
          (coord) => new AMapInstance.LngLat(coord[0], coord[1])
        );
        AMap.convertFrom(points, "gps", (status, result) => {
          if (status === "complete") {
            const convertedPoints = result.locations.map((loc) => [
              loc.lng,
              loc.lat,
            ]);
            resolve(convertedPoints);
          } else {
            reject(new Error(`坐标转换失败: ${result.info}`));
          }
        });
      })
      .catch((e) => {
        reject(e);
      });
  });
};
onBeforeUnmount(() => {
  // 清理资源
  map?.destroy();
  markers.forEach((marker) => {
    marker.setMap(null);
  });
});
</script>

<template>
  <div id="container"></div>
  <div class="search-container">
    <!-- POI查询 -->
    <div class="search-card">
      <label for="poiName" class="search-label">POI查询</label>
      <div class="input-wrapper">
        <input
          v-model="query.poiName"
          type="text"
          id="poiName"
          placeholder="输入 POI 名称"
          class="input-field"
        />
        <button @click="handlePOISearch" class="btn-submit">查询POI</button>
      </div>
    </div>

    <div v-if="poiResults.length" class="results">
      <h3>POI查询结果</h3>
      <ul>
        <li
          v-for="(item, index) in poiResults"
          :key="index"
          class="result-item"
        >
          <p><strong>名称：</strong>{{ item.name }}</p>
          <p><strong>地址：</strong>{{ item.address }}</p>
          <p><strong>类型：</strong>{{ item.type }}</p>
          <!-- 定位按钮 -->
          <button
            @click="handleLocate(item.longitude, item.latitude, item.name)"
            class="btn-locate"
          >
            查看
          </button>
        </li>
      </ul>
    </div>

    <!-- 道路查询 -->
    <div class="search-card">
      <label for="roadName" class="search-label">道路查询</label>
      <div class="input-wrapper">
        <input
          v-model="query.roadName"
          type="text"
          id="roadName"
          placeholder="输入 道路 名称"
          class="input-field"
        />
        <button @click="handleRoadSearch" class="btn-submit">查询道路</button>
      </div>
    </div>

    <div v-if="roadResults.length" class="results">
      <h3>道路查询结果</h3>
      <ul>
        <li
          v-for="(road, index) in roadResults"
          :key="index"
          class="result-item"
        >
          <p><strong>名称：</strong>{{ road.name }}</p>
          <p><strong>类型：</strong>{{ road.type }}</p>
          <!-- 定位按钮 -->
          <button @click="handleLocateRoad(road)" class="btn-locate">
            查看
          </button>
        </li>
      </ul>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>

  <!-- 移动显隐按钮到左上角 -->
  <div class="layer-toggle-container">
    <!-- 新增的开关 -->
    <div class="switch-container">
      <label class="switch">
        <input type="checkbox" @change="handleBridgeToggle" />
        <span class="slider"></span>
      </label>
      <span>桥梁</span>
    </div>

    <div class="switch-container">
      <label class="switch">
        <input type="checkbox" @change="handleKouanToggle" />
        <span class="slider"></span>
      </label>
      <span>口岸</span>
    </div>

    <div class="switch-container">
      <label class="switch">
        <input type="checkbox" @change="handleMergeToggle" />
        <span class="slider"></span>
      </label>
      <span>居民点</span>
    </div>

    <div class="switch-container">
      <label class="switch">
        <input type="checkbox" @change="handleTowersToggle" />
        <span class="slider"></span>
      </label>
      <span>塔营地</span>
    </div>
  </div>
</template>

<style scoped>
#container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
}

/* 查询框容器 */
.search-container {
  position: fixed;
  top: 80px;
  right: 20px;
  width: 350px;
  padding: 20px;
  border-radius: 8px;
  background-color: #fff !important; /* 强制背景色 */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
  z-index: 2;
  font-family: Arial, sans-serif;
}

@media (max-width: 768px) {
  .search-container {
    width: 100%;
    right: 0;
    left: 0;
    margin: 0 auto;
    top: 10px;
    padding: 15px;
  }
}

/* 查询卡片样式 */
.search-card {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ddd !important;
  border-radius: 10px;
  background-color: #f9f9f9 !important; /* 强制背景色 */
  transition: background-color 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.052) !important;
  color: #333 !important; /* 强制文字颜色 */
}

.search-card:hover {
  background-color: #f0f4f8 !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.search-label {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
  display: block;
  color: #333 !important; /* 强制文字颜色 */
}

/* 输入框和按钮的容器 */
.input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-field {
  padding: 10px;
  font-size: 14px;
  border: 1px solid #ddd !important;
  border-radius: 5px;
  flex-grow: 1;
  transition: border-color 0.3s ease;
  background-color: #ffffff !important; /* 强制背景色 */
  color: #000 !important; /* 强制文字颜色 */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.input-field:focus {
  border-color: #007bff !important;
  outline: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

button {
  padding: 12px 20px;
  background-color: #007bff !important;
  color: white !important;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: auto;
}

button:hover {
  background-color: #0056b3 !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

button:active {
  background-color: #003d7a !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 加载中、错误信息 */
.loading,
.error {
  color: #ff5733 !important;
  font-size: 14px;
  margin-top: 10px;
  padding: 10px;
  border-radius: 5px;
  background-color: #ffefef !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* 查询结果展示 */
.results {
  margin-top: 20px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ddd !important;
  border-radius: 8px;
  background-color: #fff !important; /* 强制背景色 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  color: #000 !important; /* 强制文字颜色 */
}

.result-item {
  padding: 15px;
  border-bottom: 1px solid #ddd !important;
  border-radius: 8px;
  margin-bottom: 15px;
  background-color: #fafafa !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background-color: #f0f4f8 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.result-item p {
  margin: 5px 0;
  font-size: 14px;
  color: #333 !important; /* 强制文字颜色 */
}

/* 移动显隐按钮到左上角 */
.layer-toggle-container {
  position: fixed;
  top: 80px;
  left: 250px;
  z-index: 3;
  background-color: #f5f5f5 !important; /* 强制背景色 */
  padding: 15px !important;
  border-radius: 10px !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
  width: 180px !important;
  font-family: Arial, sans-serif;
}

/* 开关容器样式 */
.switch-container {
  display: flex;
  align-items: center;
  justify-content: space-between; /* 文字和开关紧挨着 */
  margin-bottom: 10px; /* 增加间距 */
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
  margin-right: 10px; /* 增加开关和文字之间的间距 */
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #2196f3 !important;
}

input:checked + .slider:before {
  transform: translateX(26px) !important;
}

.slider.round {
  border-radius: 34px;
}

.slider.round:before {
  border-radius: 50%;
}

/* 文字标签样式 */
.switch-container span {
  font-size: 20px !important; /* 增加字体大小 */
  color: #333 !important;
  margin-left: 0; /* 文字和开关紧挨着 */
  flex-grow: 1; /* 使文字标签占据剩余空间 */
  font-family: "黑体", sans-serif; /* 改为黑体 */
}

/* 鼠标悬停效果 */
.switch-container:hover .slider {
  background-color: #bfbfbf !important;
}

.switch-container:hover input:checked + .slider {
  background-color: #1e88e5 !important;
}
</style>
