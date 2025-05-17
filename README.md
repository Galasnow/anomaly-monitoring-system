<div align="center">
    <img src="https://img.shields.io/badge/Vue-3.4.27-brightgreen.svg"/>
    <img src="https://img.shields.io/badge/Vite-5.2.11-green.svg"/>
    <img src="https://img.shields.io/badge/Element Plus-2.7.3-blue.svg"/>
    <img src="https://img.shields.io/badge/license-MIT-green.svg"/>
    <a href="https://gitee.com/youlaiorg" target="_blank">
        <img src="https://img.shields.io/badge/Author-有来开源组织-orange.svg"/>
    </a>
    <div align="center"> 中文 | <a href="./README.en-US.md">English</div>
</div>

![](https://foruda.gitee.com/images/1708618984641188532/a7cca095_716974.png "rainbow.png")

<div align="center">
  <a target="_blank" href="http://vue3.youlai.tech">👀 在线预览</a> |  <a target="_blank" href="https://juejin.cn/post/7228990409909108793">📖 阅读文档</a>  
</div>

## 说明

基础框架由有来开源组织提供，仅限于学习和交流。

## 如何使用

- **环境准备**：

| 环境 | 名称版本 | 下载地址 | 环境配置 |
| ---------- | :---------------- | --------------- | --------------- |
| **开发工具**| VSCode | [官网下载](https://code.visualstudio.com/Download)/[仓库下载]| 安装插件：1.Vue - Official(必装)  2.VSCode智能推荐插件(可选，VSCode打开项目后左下角会自动弹出推荐插件弹窗,点击安装即可) |
| **运行环境**| Node ≥18(项目使用版本为v18.20.4)| [镜像下载](https://nodejs.cn/en/download/prebuilt-installer)/[仓库下载]| [点击跳转到环境配置页面](https://zhuanlan.zhihu.com/p/638944654) |

项目软件清单:

| 名称                | 分类 | 安装版本                                         | 描述                                   |
|-------------------|----|:---------------------------------------------|--------------------------------------|
| **JAVA环境**        | 后端 | jdk-8u421-windows-x64.exe                    | Tomcat本地服务器/数据库环境依赖                  |
| **Tomcat服务器**     | 后端 | apache-tomcat-9.0.95-windows-x64.zip         | 本地服务器,代理本地数据和Geoserver数据,为前端提供访问接口   |
| **PostgreSQL**    | 后端 | postgresql-16.4-1-windows-x64.exe            | 数据库                                  |
| **PostGIS**       | 后端 | postgis-bundle-pg16x64-setup-3.4.2-1.exe     | 数据库插件,使数据库可以添加地理数据                   |
| **GeoServer**     | 后端 | geoserver-2.19.7-war.zip                     | 代理和发布地理数据                            |
| **Miniconda3**    | 后端 | Miniconda3-py38_23.11.0-2-Windows-x86_64.exe | python环境版本3.8.20,为FastAPI和本地执行脚本提供环境 |
| **Pycharm**       | 后端 | 2024.1                                       | 后端开发IDE                              |
| **NodeJS**        | 前端 | node-v18.20.4-x64.msi                        | 前端环境                                 |
| **VS Code**       | 前端 | VSCodeUserSetup-x64-1.94.2.exe               | 前端开发IDE                              |
| **QGIS**          | 其他 | QGIS-OSGeo4W-3.34.11-1.msi                   | 地理数据处理软件                             |
| **7zip**          | 其他 | 7z2408-x64.exe                               | 解压软件                                 |
| **GitHubDesktop** | 其他 | GitHubDesktopSetup-x64.exe                   | git软件                                |
| **frp**           | 其他 | frp_0.60.0                                   | 内网穿透                                 |


- **项目启动**：

```bash
# 克隆代码
git clone https://gitee.com/Aalana/vue3-webgis.git
或者直接下载zip文件到本地

# 切换目录
cd vue3-webgis

# 设置镜像源(可选)
npm config set registry https://registry.npmmirror.com

# 安装 pnpm
npm install pnpm -g

# 安装依赖
pnpm install

#(如果无法使用cesium,请使用下面命令重新安装)
pnpm i -D vite-plugin-cesium
pnpm i -S cesium
pnpm install @cesium-china/cesium-map

# 启动运行
pnpm run dev
```

- **如何自定义页面**：
-- 按照自己的需求自定义/vue3-webgis/src/views/mypages/page1.vue页面文件内容,即可实现页面自定义  
-- 可以参考/vue3-webgis/src/views/test/下的调用示例  


- **页面不够用怎么办**：
1. 在/vue3-webgis/src/router/index.ts文件中添加新页面的访问路径，如在第92行添加下面的内容即可添加一个新的“页面4”访问路由
```bash    
      {
        path: "page4",
        name: "page4",
        component: () => import("@/views/mypages/page4.vue"),
        meta: {
          title: "页面4",
        },
      },
```
2. 在/vue3-webgis/src/views/mypages/路径下新建自定义页面文件page4.vue

- **其他**：
1. 如果采用了其他WebGIS框架（Leaflet、OpenLayers、Mapbox、three.js等），以及其他本项目中未安装的库，请记录并反馈
2. （重要）框架无法直接加载shp,tiff等数据，仅支持GeoJSON、png/jpg等格式。如数据量极少，或不需要坐标信息，在页面中仅作展示，可将图片转为png/jpg等格式；shp通过QGis转为GeoJSON格式（注意：导出GeoJSON时编码格式为utf-8，投影CRS为EPSG:3857或EPSG:4326）。（推荐）如数据量较大或需要叠加底图，可在本地部署geoServer服务来加载shp，tiff等格式的数据，详细部署步骤参考*部署geoServer*。
3. 请将申请好的API密钥放到文件/vue3-webgis/my_package.json文件中，需要使用引入即可;或者在需要调用的文件中显式设置
4. 如需进行实时处理或其他问题，请及时沟通。

- **部署geoServer**：
1. 安装java环境
    -- 官网下载[jdk-8u421-windows-x64.exe](https://www.oracle.com/cn/java/technologies/downloads/#java8-windows)/[直链下载](https://sourceforge.net/projects/tomato-extra/files/apps/jdk-8u421-windows-x64.exe)||[点击查看如何配置java环境](https://blog.csdn.net/weixin_45496087/article/details/139502310)

2. 配置geoServer服务
    -- 点击下载[geoserver-2.19.7](https://sourceforge.net/projects/geoserver/files/GeoServer/2.19.7/geoserver-2.19.7-bin.zip/download)||[点击查看如何配置geoServer](https://blog.csdn.net/u010792039/article/details/139135392)

3. 添加shp或者tiff文件并发布
    -- [点击查看如何添加本地shp和tiff文件](https://blog.csdn.net/qq_27816785/article/details/132754740)

4. 添加发布完成后，在项目中通过cesium等其他WebGIS组件即可访问

![](https://foruda.gitee.com/images/1708618984641188532/a7cca095_716974.png "rainbow.png")

## 项目简介

[vue3-element-admin](https://gitee.com/youlaiorg/vue3-element-admin) 是基于 Vue3 + Vite5+ TypeScript5 + Element-Plus + Pinia 等主流技术栈构建的免费开源的后台管理前端模板（配套[后端源码](https://gitee.com/youlaiorg/youlai-boot)）。


## 项目特色

- **简洁易用**：基于 [vue-element-admin](https://gitee.com/panjiachen/vue-element-admin) 升级的 Vue3 版本，无过渡封装 ，易上手。

- **数据交互**：同时支持本地 `Mock` 和线上接口，配套 [Java 后端源码](https://gitee.com/youlaiorg/youlai-boot)和[在线接口文档](https://www.apifox.cn/apidoc/shared-195e783f-4d85-4235-a038-eec696de4ea5)。

- **权限管理**：用户、角色、菜单、字典、部门等完善的权限系统功能。

- **基础设施**：动态路由、按钮权限、国际化、代码规范、Git 提交规范、常用组件封装。

- **持续更新**：自2021年起，该项目持续开源更新，实时更新工具和依赖，积累了广泛的用户群体。



## 项目预览

![明亮模式](https://foruda.gitee.com/images/1709651876583793739/0ba1ee1c_716974.png)

![暗黑模式](https://foruda.gitee.com/images/1709651875494206224/2a2b0b53_716974.png)

![接口文档](https://foruda.gitee.com/images/1687755822857820115/96054330_716974.png)

## 项目地址

| 项目 | Gitee                                                        | Github                                                       | GitCode                                                      |
| ---- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 前端 | [vue3-element-admin](https://gitee.com/youlaiorg/vue3-element-admin) | [vue3-element-admin](https://github.com/youlaitech/vue3-element-admin) | [vue3-element-admin](https://gitcode.net/youlai/vue3-element-admin) |
| 后端 | [youlai-boot](https://gitee.com/youlaiorg/youlai-boot)       | [youlai-boot](https://github.com/haoxianrui/youlai-boot.git) | [youlai-boot](https://gitcode.net/youlai/youlai-boot)        |


## 项目部署

```bash
# 项目打包
pnpm run build

# 上传文件至远程服务器
将打包生成在 `dist` 目录下的文件拷贝至 `/usr/share/nginx/html` 目录

# nginx.cofig 配置
server {
	listen     80;
	server_name  localhost;
	location / {
			root /usr/share/nginx/html;
			index index.html index.htm;
	}
	# 反向代理配置
	location /prod-api/ {
            # vapi.youlai.tech 替换后端API地址，注意保留后面的斜杠 /
            proxy_pass http://vapi.youlai.tech/; 
	}
}
```

## 本地Mock

项目同时支持在线和本地 Mock 接口，默认使用线上接口，如需替换为 Mock 接口，修改文件 `.env.development` 的 `VITE_MOCK_DEV_SERVER` 为  `true` **即可**。

## 后端接口

> 如果您具备Java开发基础，按照以下步骤将在线接口转为本地后端接口，创建企业级前后端分离开发环境，助您走向全栈之路。

1. 获取基于 `Java` 和 `SpringBoot` 开发的后端 [youlai-boot](https://gitee.com/youlaiorg/youlai-boot.git) 源码。
2. 根据后端工程的说明文档 [README.md](https://gitee.com/youlaiorg/youlai-boot#%E9%A1%B9%E7%9B%AE%E8%BF%90%E8%A1%8C) 完成本地启动。
3. 修改 `.env.development` 文件中的 `VITE_APP_API_URL` 的值，将其从 http://vapi.youlai.tech 更改为 http://localhost:8989。


## 注意事项

- **自动导入插件自动生成默认关闭**

  模板项目的组件类型声明已自动生成。如果添加和使用新的组件，请按照图示方法开启自动生成。在自动生成完成后，记得将其设置为 `false`，避免重复执行引发冲突。

  ![](https://foruda.gitee.com/images/1687755823137387608/412ea803_716974.png)

- **项目启动浏览器访问空白**

  请升级浏览器尝试，低版本浏览器内核可能不支持某些新的 JavaScript 语法，比如可选链操作符 `?.`。

- **项目同步仓库更新升级**

  项目同步仓库更新升级之后，建议 `pnpm install` 安装更新依赖之后启动 。

- **项目组件、函数和引用爆红**

	重启 VSCode 尝试

- **其他问题**

  如果有其他问题或者建议，建议 [ISSUE](https://gitee.com/youlaiorg/vue3-element-admin/issues/new)



## 项目文档

- [基于 Vue3 + Vite + TypeScript + Element-Plus 从0到1搭建后台管理系统](https://blog.csdn.net/u013737132/article/details/130191394)

- [ESLint+Prettier+Stylelint+EditorConfig 约束和统一前端代码规范](https://blog.csdn.net/u013737132/article/details/130190788)
- [Husky + Lint-staged + Commitlint + Commitizen + cz-git 配置 Git 提交规范](https://blog.csdn.net/u013737132/article/details/130191363)


## 提交规范

执行 `pnpm run commit` 唤起 git commit 交互，根据提示完成信息的输入和选择。

![](https://foruda.gitee.com/images/1687755823165218215/c1705416_716974.png)


## 项目统计

![Alt](https://repobeats.axiom.co/api/embed/aa7cca3d6fa9c308fc659fa6e09af9a1910506c3.svg "Repobeats analytics image")


Thanks to all the contributors!

[![contributors](https://contrib.rocks/image?repo=youlaitech/vue3-element-admin)](https://github.com/youlaitech/vue3-element-admin/graphs/contributors)


## 交流群🚀

> **关注「有来技术」公众号，获取交流群二维码。**
>
> 如果交流群的二维码过期，请加微信(haoxianrui)并备注「前端」、「后端」或「全栈」以获取最新二维码。
>
> 为确保交流群质量，防止营销广告人群混入，我们采取了此措施。望各位理解！

| 公众号 | 交流群 |
|:----:|:----:|
| ![有来技术公众号二维码](https://foruda.gitee.com/images/1687689212187063809/3c69eaee_716974.png) | ![交流群二维码](https://foruda.gitee.com/images/1687689212139273561/6a65ef69_716974.png) |


2. 下载并配置Tomcat
    -- 点击下载[apache-tomcat-9.0.96-windows-x64.zip](https://dlcdn.apache.org/tomcat/tomcat-9/v9.0.96/bin/apache-tomcat-9.0.96-windows-x64.zip)[点击查看Tomcat环境配置](https://blog.csdn.net/qq_42257666/article/details/105701914)
