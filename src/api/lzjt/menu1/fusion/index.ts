import request from "@/utils/request";
import { FusionRequest } from "./model";
import { FileInfo } from "../../../file/model";

class FusionAPI {
  /**
   * 在服务器端执行融合脚本
   *
   * @param urls 两张影像的URL地址
   */
  static startFusion(urls: FusionRequest) {
    return request<any, FileInfo>({
      url: "/api/v1/fusion",
      method: "post",
      data: urls,
    });
  }
}

export default FusionAPI;
