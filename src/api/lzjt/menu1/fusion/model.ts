/**
 * 多源异构数据融合API类型声明
 */

// 定义一个枚举类型，用于区分不同场景下的数据
export enum FusionType {
  Fusion_SAR = "Fusion_SAR", // mss-sar融合
  Fusion_IR_IMG = "Fusion_IR_IMG", // vi-ir图片融合
  Fusion_IR_VIDEO = "Fusion_IR_VIDEO", // vi-ir视频融合
  Change_Detection = "Change_Detection", //变化检测
  Satellite_Visibility = "Satellite_Visibility", // 卫星可见性分析
  Other = "Other",
}

// 表示脚本执行请求的接口
export interface FusionRequest {
  Image1_name: string;
  Image2_name: string;
  type: FusionType; // flag字段，用于区分不同场景
}
