<template>
  <div>
    <div id="cesiumContainer"></div>
    <Popup
      :visible="isPopupVisible"
      :videoUrls="videoUrls"
      :deviceNames="deviceNames"
      :timestamps="timestamps"
      :location="location"
      @close="handlePopupClose"
    />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import * as Cesium from "cesium";
import {
  AMapImageryProvider,
  BaiduImageryProvider,
  GeoVisImageryProvider,
  GoogleImageryProvider,
  TdtImageryProvider,
  TencentImageryProvider,
} from "@cesium-china/cesium-map";
import { cesium_token } from "../../../../my_package.json";
import Popup from "@/components/Popup/index.vue"; // 引入 Popup 组件
import CircleRippleMaterialProperty from "@/assets/CircleRippleMaterial"; // 导入材质类
// import Taxkorgan from "../test/other_Taxkorgan_province.json";

// http://127.0.0.1:8989
// http://47.108.151.251:13140
const baseImageUrl = "http://127.0.0.1:13140/localdata";
const category = "底图选择";
let cesium_viewer = null;
const rippleSize = ref(1); // 用于存储波纹的大小系数
let customEntities = []; // 用来存储多个自定义图标的实体
let customellipseEntities = [];
let isPopupVisible = ref(false); // 用来标记弹出框是否已显示
let videoUrls = ref([]);
let deviceNames = ref([]);
let timestamps = ref([]);
let location = ref("");

// 关闭弹出框
const handlePopupClose = () => {
  isPopupVisible.value = false;
};

onMounted(async () => {
  Cesium.Ion.defaultAccessToken = cesium_token;

  var imageryViewModels = [];
  var AMapImagery = new Cesium.ProviderViewModel({
    name: "高德地图",
    category: `${category}`,
    tooltip: "由高德地图提供服务",
    iconUrl: `${baseImageUrl}/icos/AMap.png`,
    creationFunction: function () {
      return new AMapImageryProvider({
        style: "img", // style: img(卫星)、elec(普通)、cva(路网标注)
        crs: "WGS84", // 使用84坐标系，默认为：GCJ02
      });
    },
  });

  var BaiduImagery = new Cesium.ProviderViewModel({
    name: "百度地图",
    category: `${category}`,
    tooltip: "由百度地图提供服务",
    iconUrl: `${baseImageUrl}/icos/Baidu.png`,
    creationFunction: function () {
      return new BaiduImageryProvider({
        style: "img", // style: img(卫星)、vec(矢量标注)、normal(路网标注)、dark
        crs: "WGS84", // 使用84坐标系，默认为：BD09
      });
    },
  });

  var TdtImagery = new Cesium.ProviderViewModel({
    name: "天地图",
    category: `${category}`,
    tooltip: "由天地图提供服务",
    iconUrl: `${baseImageUrl}/icos/Tdt.png`,
    creationFunction: function () {
      return new TdtImageryProvider({
        style: "img", //style: vec(最新版地图)、cva(地理名称)、img(卫星)、cia(路网+地理名称)、ter(地形)
        key: "8b207a527da69c7a32f636801fa194d4", // 需去相关地图厂商申请
      });
    },
  });

  var TencentImagery = new Cesium.ProviderViewModel({
    name: "腾讯地图",
    category: `${category}`,
    tooltip: "由国腾讯提供",
    iconUrl: `${baseImageUrl}/icos/Tencent.png`,
    creationFunction: function () {
      return new TencentImageryProvider({
        style: "img", //style: img、1：经典
        crs: "WGS84", // 使用84坐标系，默认为：GCJ02,
      });
    },
  });

  var esriMapModel = new Cesium.ProviderViewModel({
    name: "Esri World Imagery",
    category: `${category}`,
    iconUrl: `${baseImageUrl}/icos/esri.png`,
    tooltip: "ArcGIS 地图服务",
    creationFunction: function () {
      return Cesium.ArcGisMapServerImageryProvider.fromBasemapType(
        Cesium.ArcGisBaseMapType.SATELLITE,
        {
          enablePickFeatures: false,
        }
      );
    },
  });

  var BingMapModel = new Cesium.ProviderViewModel({
    name: "Bing Maps Aerial",
    category: `${category}`,
    iconUrl: `${baseImageUrl}/icos/Bing.png`,
    tooltip: "Bing Maps aerial imagery, provided by Cesium ion",
    creationFunction: function () {
      return Cesium.createWorldImageryAsync({
        style: Cesium.IonWorldImageryStyle.AERIAL,
      });
    },
  });
  imageryViewModels.push(esriMapModel);
  imageryViewModels.push(BingMapModel);
  imageryViewModels.push(TdtImagery);
  imageryViewModels.push(AMapImagery);
  imageryViewModels.push(BaiduImagery);
  imageryViewModels.push(TencentImagery);

  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    terrain: Cesium.Terrain.fromWorldTerrain(),
    animation: false, // 是否打开创建动画小控件，即左下角的仪表
    baseLayerPicker: true, // 是否显示图层选择器
    fullscreenButton: false, // 是否显示全屏按钮
    geocoder: true, // 是否显示Geocoder(右上角的查询按钮)
    homeButton: true, // 是否显示Home按钮
    infoBox: false, // 是否显示信息框
    maximumRenderTimeChange: Infinity, // 请求新帧的时间
    navigationHelpButton: false, // 是否显示右上角帮助按钮
    navigationInstructionsInitiallyVisible: false, //是否显示帮助信息
    // requestRenderMode: true, // 显式渲染，渲染优化
    orderIndependentTranslucency: false, // 设置背景透明
    sceneMode: Cesium.SceneMode.SCENE3D, //3d视角展示
    sceneModePicker: false, // 是否显示三维地球/二维地图选择器
    selectionIndicator: true, // 是否显示选取指示器
    shadows: false, //光照的阴影效果
    shouldAnimate: true, //执行模型动画
    showRenderLoopErrors: false, // 是否显示渲染错误
    timeline: false, // 是否关闭时间轴
    vrButton: false, // 是否显示VR控件
    imageryProviderViewModels: imageryViewModels,
    selectedImageryProviderViewModel: esriMapModel,
    terrainProviderViewModels: [], //禁用地形选择器
  });

  // 标注图层
  cesium_viewer.imageryLayers.addImageryProvider(
    new TdtImageryProvider({
      style: "cia", // 路网标注
      key: "8b207a527da69c7a32f636801fa194d4",
    })
  );

  cesium_viewer.scene.frameState.creditDisplay.container.style.display = "none";
  cesium_viewer.scene.globe.depthTestAgainstTerrain = false; // 设置为 false 禁用地形深度测试

  // 监听相机位置变化，根据相机高度调整波纹大小
  cesium_viewer.scene.preRender.addEventListener(() => {
    const cameraPosition = cesium_viewer.camera.positionCartographic;
    const height = cameraPosition.height; // 获取相机高度
    rippleSize.value = Math.max(0.01, height / 560000); // 根据相机高度调整波纹的大小，避免波纹过小
    rippleSize.value = Math.min(20, rippleSize.value);
  });

  // 设置多个自定义图标
  const positions = [
    {
      lon: 74.5889,
      lat: 37.06,
      location: "自定义地点1",
      videoUrls: [
        `${baseImageUrl}/static/TNO_Dataset/soldier_behind_smoke_1/VI.bmp`,
        `${baseImageUrl}/static/TNO_Dataset/soldier_behind_smoke_1/IR.bmp`,
        `${baseImageUrl}/static/TNO_Dataset/soldier_behind_smoke_1/result.jpg`,
      ],
      deviceNames: ["设备1 真彩色画面", "设备2 红外画面", "系统融合画面"],
      timestamps: ["2024-12-12 18:09", "2024-12-12 18:09", "2024-12-12 18:10"],
      label: "警",
      color: "#ff0000",
    },
    {
      lon: 75.481171,
      lat: 36.746794,
      location: "自定义地点2",
      videoUrls: [
        `${baseImageUrl}/static/TNO_Dataset/bunker/VI.bmp`,
        `${baseImageUrl}/static/TNO_Dataset/bunker/IR.bmp`,
        `${baseImageUrl}/static/TNO_Dataset/bunker/result.jpg`,
      ],
      deviceNames: ["设备2"],
      timestamps: ["2024-12-12 18:10"],
      label: "预",
      color: "#ffa500",
    },
    {
      lon: 75.007908,
      lat: 37.547564,
      location: "自定义地点3",
      videoUrls: [
        `${baseImageUrl}/static/INO_Dataset/MainEntrance/VI.mp4`,
        `${baseImageUrl}/static/INO_Dataset/MainEntrance/IR.mp4`,
        `${baseImageUrl}/static/INO_Dataset/MainEntrance/result.mp4`,
      ],
      deviceNames: ["设备3"],
      timestamps: ["2024-12-12 18:11"],
      label: "预",
      color: "#ffa500",
    },
  ];

  const pinBuilder = new Cesium.PinBuilder();
  positions.forEach((pos, index) => {
    const entity = cesium_viewer.entities.add({
      name: `预警地点${index + 1}`,
      position: Cesium.Cartesian3.fromDegrees(pos.lon, pos.lat),
      billboard: {
        image: pinBuilder
          .fromText(pos.label, Cesium.Color.fromCssColorString(pos.color), 48)
          .toDataURL(),
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        // disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    });
    customEntities.push({ entity, ...pos });

    const ellipseEntity = cesium_viewer.entities.add({
      name: `波纹效果${index + 1}`,
      position: Cesium.Cartesian3.fromDegrees(pos.lon, pos.lat),
      ellipse: {
        height: 0,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        semiMinorAxis: new Cesium.CallbackProperty(
          () => 20000 * rippleSize.value,
          false
        ),
        semiMajorAxis: new Cesium.CallbackProperty(
          () => 20000 * rippleSize.value,
          false
        ),
        material: new CircleRippleMaterialProperty({
          color: Cesium.Color.fromCssColorString(pos.color),
          speed: 10,
          count: 3,
          gradient: 0.5,
        }),
      },
      allowPicking: false, // 禁用选中
    });
    customEntities.push({ entity: ellipseEntity, ...pos });
  });

  // 设置点击事件
  const handler = new Cesium.ScreenSpaceEventHandler(cesium_viewer.canvas);
  handler.setInputAction(function (click) {
    const pickedObject = cesium_viewer.scene.pick(click.position);

    if (Cesium.defined(pickedObject)) {
      const pickedEntity = customEntities.find(
        (item) => item.entity === pickedObject.id
      );
      if (pickedEntity) {
        location.value = pickedEntity.location;
        videoUrls.value = pickedEntity.videoUrls;
        deviceNames.value = pickedEntity.deviceNames;
        timestamps.value = pickedEntity.timestamps;
        isPopupVisible.value = true;
      } else {
        isPopupVisible.value = false;
      }
    } else {
      isPopupVisible.value = false;
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

  // Cesium.GeoJsonDataSource.load(Taxkorgan, {
  //   stroke: Cesium.Color.RED, // 边框颜色
  //   fill: Cesium.Color.RED.withAlpha(0), // 填充颜色及透明度
  //   strokeWidth: 500, // 边框宽度
  //   markerSize: 10, // 标记点大小（如果有点数据）
  // })
  //   .then((geoJsonDataSource) => {
  //     // 添加到 Viewer
  //     cesium_viewer.dataSources.add(geoJsonDataSource);

  //     // 放大到数据区域
  //     // cesium_viewer.flyTo(geoJsonDataSource);
  //   })
  //   .catch((error) => {
  //     console.error("GeoJSON 加载失败:", error);
  //   });

  cesium_viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(76.0, 36.5, 1000000),
  });
});

onUnmounted(() => {
  cesium_viewer?.destroy();
});
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100vh;
  margin: 0;
  padding: 0;
  position: relative;
}

#cesiumContainer {
  width: 100%;
  height: 100%;
  position: absolute;
}
</style>
