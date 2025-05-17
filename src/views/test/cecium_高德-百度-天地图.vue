<!-- @src/views/dashboard/高德-百度-天地图.vue -->
<template>
  <div id="cesiumContainer"></div>
</template>

<script setup lg="ts">
import { onMounted, onUnmounted } from "vue";
import * as Cesium from "cesium";
import {
  AMapImageryProvider,
  BaiduImageryProvider,
  GeoVisImageryProvider,
  GoogleImageryProvider,
  TdtImageryProvider,
  TencentImageryProvider,
} from "@cesium-china/cesium-map";
import { cesium_token, GeoVis_token } from "../../../my_package.json";
import Taxkorgan from "./other_Taxkorgan_province.json";

const baseImageUrl = "http://localhost:13140/localdata/images_maps";
const category = "底图选择";
let cesium_viewer = null;

onMounted(async () => {
  Cesium.Ion.defaultAccessToken = cesium_token;

  var imageryViewModels = [];

  var AMapImagery = new Cesium.ProviderViewModel({
    name: "高德地图",
    category: `${category}`,
    tooltip: "由高德地图提供服务",
    iconUrl: `${baseImageUrl}/AMap.png`,
    creationFunction: function () {
      return new AMapImageryProvider({
        style: "cva", // style: img(卫星)、elec(普通)、cva(路网标注)
        crs: "WGS84", // 使用84坐标系，默认为：GCJ02
      });
    },
  });

  var BaiduImagery = new Cesium.ProviderViewModel({
    name: "百度地图",
    category: `${category}`,
    tooltip: "由百度地图提供服务",
    iconUrl: `${baseImageUrl}/Baidu.png`,
    creationFunction: function () {
      return new BaiduImageryProvider({
        style: "vec", // style: img(卫星)、vec(矢量标注)、normal(路网标注)、dark
        crs: "WGS84", // 使用84坐标系，默认为：BD09
      });
    },
  });

  var TdtImagery = new Cesium.ProviderViewModel({
    name: "天地图",
    category: `${category}`,
    tooltip: "由天地图提供服务",
    iconUrl: `${baseImageUrl}/Tdt.png`,
    creationFunction: function () {
      return new TdtImageryProvider({
        style: "cia", //style: vec(最新版地图)、cva(地理名称)、img(卫星)、cia(路网+地理名称)、ter(地形)
        key: "8b207a527da69c7a32f636801fa194d4", // 需去相关地图厂商申请
      });
    },
  });

  var TencentImagery = new Cesium.ProviderViewModel({
    name: "腾讯地图",
    category: `${category}`,
    tooltip: "由国腾讯提供",
    iconUrl: `${baseImageUrl}/Tencent.png`,
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
    iconUrl: `${baseImageUrl}/esri.png`,
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
    iconUrl: `${baseImageUrl}/Bing.png`,
    tooltip: "Bing Maps aerial imagery, provided by Cesium ion",
    creationFunction: function () {
      return Cesium.createWorldImageryAsync({
        style: Cesium.IonWorldImageryStyle.AERIAL,
      });
    },
  });

  {
    // 由于某些原因无法使用
    // var GeoVisImagery = new Cesium.ProviderViewModel({
    //   name: "星球地图",
    //   tooltip: "由中科星图提供服务",
    //   iconUrl: `${baseImageUrl}/GeoVis.png`,
    //   creationFunction: function () {
    //     return new GeoVisImageryProvider({
    //       style: "img", //style: img、vec(标注)、ter(地形), cia(路网+地理名称),cat(路网+地理名称),
    //       key: GeoVis_token, // 需去相关地图厂商申请
    //       format: "png", //format:png、webp(用于style为img)
    //     });
    //   },
    // });
    // var GoogleImagery = new Cesium.ProviderViewModel({
    //   name: "谷歌地图",
    //   tooltip: "由国内第三方Google Earth代理提供",
    //   iconUrl: "./sampleData/images/tianditu.jpg",
    //   creationFunction: function () {
    //     return new GoogleImageryProvider({
    //       style: "elec", //style: img、elec、ter,cva,img_cva
    //       crs: "WGS84", // 使用84坐标系，默认为：GCJ02, img除外
    //     });
    //   },
    // });
  }

  imageryViewModels.push(esriMapModel);
  imageryViewModels.push(BingMapModel);
  imageryViewModels.push(TdtImagery);
  imageryViewModels.push(AMapImagery);
  imageryViewModels.push(BaiduImagery);
  imageryViewModels.push(TencentImagery);
  // imageryViewModels.push(GeoVisImagery);
  // imageryViewModels.push(GoogleImagery);

  cesium_viewer = new Cesium.Viewer("cesiumContainer", {
    baseLayerPicker: true, //是否显示图层选择器
    imageryProviderViewModels: imageryViewModels,
    selectedImageryProviderViewModel: esriMapModel,
    terrainProviderViewModels: [], //禁用地形选择器
  });

  cesium_viewer.imageryLayers.addImageryProvider(
    new TdtImageryProvider({
      style: "cia", // 路网标注
      key: "8b207a527da69c7a32f636801fa194d4",
    })
  );

  // viewer.imageryLayers.removeAll();
  cesium_viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(
    Cesium.ScreenSpaceEventType.LEFT_CLICK
  );
  cesium_viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(
    Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK
  );

  // viewer.terrainProvider = await Cesium.createWorldTerrainAsync({
  //   requestVertexNormals: true,
  //   requestWaterMask: true,
  // }); // 加入地形和水纹.
  // viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider({}); // 普通底图
  // viewer.imageryLayers.remove(viewer.imageryLayers.get(0)); // 去掉初始图层
  // viewer.baseLayerPicker.viewModel.imageryProviderViewModels = [];

  // 获取图层选择器中的图层
  var imageryLayers =
    cesium_viewer.baseLayerPicker.viewModel.imageryProviderViewModels;

  // // 打印每个图层的所有属性
  // imageryLayers.forEach(function (layer) {
  //   console.log(layer); // 直接输出对象查看所有属性
  // });

  // // 打印当前选中的图层的所有属性
  // var selectedLayer = viewer.baseLayerPicker.viewModel.selectedImagery;
  // console.log(selectedLayer); // 直接输出对象查看所有属性
  // 加载 GeoJSON 文件
  Cesium.GeoJsonDataSource.load(Taxkorgan, {
    stroke: Cesium.Color.RED, // 边框颜色
    fill: Cesium.Color.RED.withAlpha(0), // 填充颜色及透明度
    strokeWidth: 3, // 边框宽度
    markerSize: 10, // 标记点大小（如果有点数据）
  })
    .then((geoJsonDataSource) => {
      // 添加到 Viewer
      cesium_viewer.dataSources.add(geoJsonDataSource);

      // 放大到数据区域
      cesium_viewer.flyTo(geoJsonDataSource);
    })
    .catch((error) => {
      console.log("Loading GeoJSON from:", "./other_Taxkorgan_province.json");
      console.error("GeoJSON 加载失败:", error);
    });
});

onUnmounted(() => {
  cesium_viewer?.destroy();
});
</script>

<style scoped>
#container {
  width: 100%;
  height: 800px;
}
</style>

<style scoped>
#cesiumContainer {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
