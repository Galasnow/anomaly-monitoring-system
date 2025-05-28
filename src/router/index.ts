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
    path: "/Taiwan_Port",
    name: "TaiwanPort",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "台海港口异常扩建动态监测",
      alwaysShow: true,
    },
    children: [
      {
        path: "page1_Taiwan_Port_all",
        name: "page1_Taiwan_Port_all",
        component: () => import("@/views/Taiwan_Port/page1_Taiwan_Port_all.vue"),
        meta: {
          title: "监测区域",
        },
      },
      {
        path: "page2_Gaoxiong_Port",
        name: "page2_Gaoxiong_Port",
        component: () => import("@/views/Taiwan_Port/page2_Gaoxiong_Port.vue"),
        meta: {
          title: "高雄港异常扩建动态监测",
        },
      },
      {
        path: "page3_Taibei_Port",
        name: "page3_Taibei_Port",
        component: () => import("@/views/Taiwan_Port/page3_Taibei_Port.vue"),
        meta: {
          title: "台北港异常扩建动态监测",
        },
      },
    ],
  },

  // 中印边境营地异常扩建动态监测
  {
    path: "/India_Base",
    name: "India_Base",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "中印边境营地异常扩建动态监测",
      icon: "",
      alwaysShow: true,
    },
    children: [
      {
        path: "page1_India_Base_all",
        name: "page1_India_Base_all",
        component: () => import("@/views/India_Base/page1_India_Base_all.vue"),
        meta: {
          title: "监测区域",
          icon: "",
        },
      },
      {
        path: "page2_Durbuk_Base",
        name: "page2_Durbuk_Base",
        component: () => import("@/views/India_Base/page2_Durbuk_Base.vue"),
        meta: {
          title: "杜尔布克营地异常扩建监测",
          icon: "",
        },
      },
      {
        path: "page3_Chummur_Base",
        name: "page3_Chummur_Base",
        component: () => import("@/views/India_Base/page3_Chummur_Base.vue"),
        meta: {
          title: "楚马要塞异常扩建监测",
          icon: "",
        },
      },
    ],
  },

  // 中印边境机场异常扩建动态监测
  {
    path: "/India_Airport",
    name: "India_Airport",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "中印边境机场异常扩建动态监测",
      icon: "",
      alwaysShow: true,
    },
    children: [
      {
        path: "page1_India_Airport_all",
        name: "page1_India_Airport_all",
        component: () => import("@/views/India_Airport/page1_India_Airport_all.vue"),
        meta: {
          title: "监测区域",
          icon: "",
        },
      },
      {
        path: "page2_Bhatinda_Air_Force_Station",
        name: "page2_Bhatinda_Air_Force_Station",
        component: () => import("@/views/India_Airport/page2_Bhatinda_Air_Force_Station.vue"),
        meta: {
          title: "比夏纳空军基地",
          icon: "",
        },
      },
      {
        path: "page3_Silchar_Airport",
        name: "page3_Silchar_Airport",
        component: () => import("@/views/India_Airport/page3_Silchar_Airport.vue"),
        meta: {
          title: "锡尔恰尔机场",
          icon: "",
        },
      },
      {
        path: "page4_Dehradun_Airport",
        name: "page4_Dehradun_Airport",
        component: () => import("@/views/India_Airport/page4_Dehradun_Airport.vue"),
        meta: {
          title: "德拉敦机场",
          icon: "",
        },
      },
      {
        path: "page5_Leh_Airport",
        name: "page5_Leh_Airport",
        component: () => import("@/views/India_Airport/page5_Leh_Airport.vue"),
        meta: {
          title: "列城机场",
          icon: "",
        },
      },
      {
        path: "page6_Lengpui_Airport",
        name: "page6_Lengpui_Airport",
        component: () => import("@/views/India_Airport/page6_Lengpui_Airport.vue"),
        meta: {
          title: "伦格普伊机场",
          icon: "",
        },
      },
      {
        path: "page7_Chabua_Air_Force_Station",
        name: "page7_Chabua_Air_Force_Station",
        component: () => import("@/views/India_Airport/page7_Chabua_Air_Force_Station.vue"),
        meta: {
          title: "贾布瓦空军基地",
          icon: "",
        },
      },
      {
        path: "page8_Shilong_Airport",
        name: "page8_Shilong_Airport",
        component: () => import("@/views/India_Airport/page8_Shilong_Airport.vue"),
        meta: {
          title: "西隆机场",
          icon: "",
        },
      },
    ],
  },

  // 中印边境营地异常扩建动态监测
  {
    path: "/Pakistan_Lake",
    name: "Pakistan_Lake",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "中巴边境冰川堰塞湖异常溃决动态监测",
      icon: "",
      alwaysShow: true,
    },
    children: [
      {
        path: "page1_Pakistan_Lake_all",
        name: "page1_Pakistan_Lake_all",
        component: () => import("@/views/Pakistan_Lake/page1_Pakistan_Lake_all.vue"),
        meta: {
          title: "监测区域",
          icon: "",
        },
      },
      {
        path: "page2_Hassanabad",
        name: "page2_Hassanabad",
        component: () => import("@/views/Pakistan_Lake/page2_Hassanabad.vue"),
        meta: {
          title: "哈萨纳巴德冰川堰塞湖",
          icon: "",
        },
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
