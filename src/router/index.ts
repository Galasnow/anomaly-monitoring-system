import type { App } from "vue";
import { createRouter, createWebHashHistory, RouteRecordRaw } from "vue-router";

export const Layout = () => import("@/layout/index.vue");

// 静态路由
export const constantRoutes: RouteRecordRaw[] = [
  {
    path: "/redirect",
    component: Layout,
    meta: { hidden: true },
    children: [
      {
        path: "/redirect/:path(.*)",
        component: () => import("@/views/redirect/index.vue"),
      },
    ],
  },

  {
    path: "/login",
    component: () => import("@/views/login/index.vue"),
    meta: { hidden: true },
  },

  {
    path: "/",
    name: "/",
    component: Layout,
    redirect: "/dashboard",
    children: [
      {
        path: "dashboard",
        component: () => import("@/views/dashboard/index.vue"),
        name: "Dashboard", // 用于 keep-alive, 必须与SFC自动推导或者显示声明的组件name一致
        // https://cn.vuejs.org/guide/built-ins/keep-alive.html#include-exclude
        meta: {
          title: "dashboard",
          icon: "homepage",
          affix: true,
          keepAlive: true,
          alwaysShow: false,
        },
      },
      {
        path: "401",
        component: () => import("@/views/error-page/401.vue"),
        meta: { hidden: true },
      },
      {
        path: "404",
        component: () => import("@/views/error-page/404.vue"),
        meta: { hidden: true },
      },
    ],
  },

  // 以下为自定义页面
  // 台海港口异常扩建动态监测
  {
    path: "/mypages",
    name: "mypages",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "台海港口异常扩建动态监测",
      alwaysShow: true,
    },
    children: [
      {
        path: "page1",
        name: "page1",
        component: () => import("@/views/mypages/page1_1.vue"),
        meta: {
          title: "监测区域",
        },
      },
      {
        path: "page2",
        name: "page2",
        component: () => import("@/views/mypages/page2.vue"),
        meta: {
          title: "台北港异常扩建动态监测",
        },
      },
      {
        path: "page3",
        name: "page3",
        component: () => import("@/views/mypages/page3.vue"),
        meta: {
          title: "高雄港异常扩建动态监测",
        },
      },
      {
        path: "page4",
        name: "page4",
        component: () => import("@/views/mypages/page2_copy.vue"),
        meta: {
          title: "读取文件夹内容",
        },
      },
      {
        path: "cesiumviewer",
        name: "cesiumviewer",
        component: () => import("@/views/mypages/page3_base.vue"),
        meta: {
          title: "Cesium",
        },
      },
    ],
  },

  // 测试页面
  {
    path: "/test",
    name: "test",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "中印边境飞机异常进出库动态监测",
      icon: "",
      alwaysShow: true,
    },
    children: [
      {
        path: "test1",
        name: "test1",
        component: () => import("@/views/test/other_显示图标.vue"),
        meta: {
          title: "图标展示1",
          icon: "",
        },
      },
      {
        path: "test2",
        name: "test2",
        component: () => import("@/views/test/other_显示图标2.vue"),
        meta: {
          title: "图标展示2",
          icon: "",
        },
      },
      {
        path: "test3",
        name: "test3",
        component: () => import("@/views/test/other_上传图片.vue"),
        meta: {
          title: "上传图片",
          icon: "",
        },
      },
      {
        path: "test4",
        name: "test4",
        component: () => import("@/views/test/cecium_加载本地wms服务.vue"),
        meta: {
          title: "加载本地wms服务",
          icon: "",
        },
      },
      {
        path: "test5",
        name: "test5",
        component: () => import("@/views/test/index.vue"),
        meta: {
          title: "模板页面",
          icon: "",
        },
      },
    ],
  },

  {
    path: "/Database",
    component: Layout,
    redirect: "noredirect",
    name: "/Database",
    meta: {
      title: "数据库管理",
      hidden: false,
      roles: ["ADMIN"],
      keepAlive: false,
      alwaysShow: false,
      params: null,
    },
    children: [
      {
        path: "/Database",
        component: () => import("@/views/menus/数据库管理.vue"),
        name: "Database",
        meta: {
          title: "中印边境机场异常扩建动态监测",
          hidden: false,
          roles: ["ADMIN"],
          keepAlive: true,
          alwaysShow: false,
          params: null,
        },
      },
    ],
  },

  // 测试页面
  {
    path: "/menu1",
    component: Layout,
    redirect: "noredirect",
    name: "Menu1",
    meta: {
      title: "中印边境营地异常扩建动态监测", //安全态势动态监测
      hidden: false,
      roles: ["ADMIN"],
      alwaysShow: false,
      params: null,
    },
    children: [
      {
        path: "menu1-1",
        component: () => import("@/views/mypages/page4.vue"),
        redirect: "noredirect",
        name: "Menu1-1",
        meta: {
          title: "关键要素挖掘",
          hidden: false,
          roles: ["ADMIN"],
          keepAlive: true,
          alwaysShow: false,
          params: null,
        },
        children: [
          {
            path: "menu1-1-1",
            component: () => import("@/views/mypages/page3.vue"),
            name: "Menu1-1-1",
            meta: {
              title: "时空数据挖掘",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
          {
            path: "menu1-1-2",
            component: () =>
              import("@/views/menus/menu1/多源异构数据融合[展示].vue"),
            name: "Menu1-1-2",
            meta: {
              title: "✅多源异构数据融合[展示]",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
          {
            path: "menu1-1-3",
            component: () =>
              import("@/views/menus/menu1/多源异构数据融合[功能].vue"),
            name: "Menu1-1-3",
            meta: {
              title: "✅多源异构数据融合[功能]",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
        ],
      },
      {
        path: "menu1-2",
        component: () => import("@/views/mypages/page4.vue"),
        redirect: "noredirect",
        name: "Menu1-2",
        meta: {
          title: "异常信息检测",
          hidden: false,
          roles: ["ADMIN"],
          keepAlive: true,
          alwaysShow: false,
          params: null,
        },
        children: [
          {
            path: "menu1-2-1",
            component: () =>
              import("@/views/menus/menu1/影像变化检测[功能].vue"),
            name: "Menu1-2-1",
            meta: {
              title: "✅影像变化检测[功能]",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
          {
            path: "menu1-2-2",
            component: () => import("@/views/menus/menu1/社交网络检测.vue"),
            name: "Menu1-2-2",
            meta: {
              title: "社交网络检测",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
          {
            path: "menu1-2-3",
            component: () => import("@/views/menus/menu1/异常变化检测.vue"),
            name: "Menu1-2-3",
            meta: {
              title: "✅异常变化检测",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
        ],
      },
    ],
  },

  // 测试页面
  {
    path: "/menu3",
    component: Layout,
    redirect: "noredirect",
    name: "Menu3",
    meta: {
      title: "南海船舶异常聚集动态监测", //安全态势互联互通
      hidden: false,
      roles: ["ADMIN"],
      alwaysShow: false,
      params: null,
    },
    children: [
      {
        path: "menu3-1",
        component: () => import("@/views/mypages/page4.vue"),
        name: "Menu3-1",
        meta: {
          title: "边境互联互通",
          hidden: false,
          roles: ["ADMIN"],
          keepAlive: true,
          alwaysShow: false,
          params: null,
        },
        children: [
          {
            path: "menu3-1-1",
            component: () => import("@/views/menus/menu3/道路网互联互通.vue"),
            name: "Menu3-1-1",
            meta: {
              title: "✅道路网互联互通",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
          {
            path: "menu3-1-2",
            component: () =>
              import("@/views/menus/menu3/卫星导航和移动通讯互联互通.vue"),
            name: "Menu3-1-2",
            meta: {
              title: "✅卫星导航和移动通讯互联互通",
              hidden: false,
              roles: ["ADMIN"],
              keepAlive: true,
              alwaysShow: false,
              params: null,
            },
          },
        ],
      },
      {
        path: "menu3-2",
        component: () => import("@/views/mypages/page3.vue"),
        name: "Menu3-2",
        meta: {
          title: "渔船搜救互联互通",
          hidden: false,
          roles: ["ADMIN"],
          keepAlive: true,
          alwaysShow: false,
          params: null,
        },
      },
    ],
  },

  // 测试页面
  {
    path: "/menu2",
    component: Layout,
    redirect: "noredirect",
    name: "Menu2",
    meta: {
      title: "南海岛礁异常扩建动态监测", //安全态势分级与情势推演
      hidden: false,
      roles: ["ADMIN"],
      alwaysShow: false,
      params: null,
    },
    children: [
      {
        path: "menu2-1",
        component: () => import("@/views/mypages/page2_Daojiao.vue"),
        name: "Menu2-1",
        meta: {
          title: "柏礁异常扩建动态监测",
          hidden: false,
          roles: ["ADMIN"],
          keepAlive: true,
          alwaysShow: false,
          params: null,
        },
      },
      {
        path: "menu2-2",
        component: () => import("@/views/menus/menu2/SAVEE.vue"),
        name: "Menu2-2",
        meta: {
          title: "南华礁异常扩建动态监测",
          hidden: false,
          roles: ["ADMIN"],
          keepAlive: true,
          alwaysShow: false,
          params: null,
        },
      },
    ],
  },

  // 海上油气平台
  {
    path: "/offshore_platform",
    component: Layout,
    redirect: "noredirect",
    name: "OffshorePlatform",
    meta: {
      title: "南海海上钻井平台异常动态监测",
      hidden: false,
      roles: ["ADMIN"],
      alwaysShow: false,
      params: null,
    },
    children: [
      {
        path: "page_area_of_platform_monitoring",
        name: "page_area_of_platform_monitoring",
        component: () =>
          import(
            "@/views/offshore_platform/page_area_of_platform_monitoring.vue"
          ),
        meta: {
          title: "监测区域",
        },
      },
      {
        path: "page_sk10_platform",
        name: "page_sk10_platform",
        component: () =>
          import("@/views/offshore_platform/page_sk10_platform.vue"),
        meta: {
          title: "Sk10海上油气平台异常动态监测",
        },
      },
    ],
  },
];

/**
 * 创建路由
 */
const router = createRouter({
  history: createWebHashHistory(),
  routes: constantRoutes,
  // 刷新时，滚动条位置还原
  scrollBehavior: () => ({ left: 0, top: 0 }),
});

// 全局注册 router
export function setupRouter(app: App<Element>) {
  app.use(router);
}

/**
 * 重置路由
 */
export function resetRouter() {
  router.replace({ path: "/login" });
}

export default router;
