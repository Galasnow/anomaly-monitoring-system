// @src/router/index.ts
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

  // 一级菜单1
  {
    path: "/menu1",
    name: "Menu1",
    component: Layout,
    redirect: "noredirect", // 不重定向, 不进行跳转
    meta: {
      title: "安全态势动态监测",
      icon: "api",
      alwaysShow: true,
      // breadcrumb: false, // 不生成面包屑
    },
    children: [
      {
        path: "menu1-1",
        name: "Menu1-1",
        redirect: "noredirect", // 不重定向, 不进行跳转
        meta: {
          title: "关键要素挖掘",
          icon: "api",
          alwaysShow: true,
          // breadcrumb: false, // 不生成面包屑
        },
        children: [
          {
            path: "menu1-1-1",
            name: "Menu1-1-1",
            component: () => import("@/views/menus/menu1/internal-doc.vue"),
            meta: {
              title: "数据库管理",
              icon: "api",
            },
          },
          {
            path: "menu1-1-2",
            name: "Menu1-1-2",
            component: () => import("@/views/menus/menu1/internal-doc.vue"),
            meta: {
              title: "时空数据挖掘",
              icon: "api",
            },
          },
          {
            path: "menu1-1-3",
            name: "Menu1-1-3",
            component: () => import("@/views/menus/menu1/internal-doc.vue"),
            meta: {
              title: "多源异构数据融合",
              icon: "api",
            },
          },
        ],
      },
      {
        path: "menu1-2",
        name: "Menu1-2",
        redirect: "noredirect", // 不重定向, 不进行跳转
        meta: {
          title: "异常信息检测",
          icon: "api",
          alwaysShow: true,
          // breadcrumb: false, // 不生成面包屑
        },
        children: [
          {
            path: "menu1-2-1",
            name: "Menu1-2-1",
            component: () => import("@/views/menus/menu2/level1.vue"),
            meta: {
              title: "影像变化检测",
              icon: "api",
            },
          },
          {
            path: "menu1-2-2",
            name: "Menu1-2-2",
            component: () => import("@/views/menus/menu2/level1.vue"),
            meta: {
              title: "社交网络检测",
              icon: "api",
            },
          },
          {
            path: "menu1-2-3",
            name: "Menu1-2-3",
            component: () => import("@/views/menus/menu2/level1.vue"),
            meta: {
              title: "异常变化检测",
              icon: "api",
            },
          },
        ],
      },
    ],
  },

  // 一级菜单2
  {
    path: "/menu2",
    name: "Menu2",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "安全态势分级",
      icon: "api",
      alwaysShow: true,
    },
    children: [
      {
        path: "menu2-1",
        name: "Menu2-1",
        redirect: "noredirect",
        meta: {
          title: "评价模型",
          icon: "api",
          alwaysShow: true,
        },
      },
      {
        path: "menu2-2",
        name: "Menu2-2",
        redirect: "noredirect",
        meta: {
          title: "定量分级研判",
          icon: "api",
          alwaysShow: true,
        },
      },
    ],
  },

  // 一级菜单3
  {
    path: "/menu3",
    name: "Menu3",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "安全态势互联互通",
      icon: "api",
      alwaysShow: true,
    },
    children: [
      {
        path: "menu3-1",
        name: "Menu3-1",
        redirect: "noredirect",
        meta: {
          title: "边境互联互通",
          icon: "api",
          alwaysShow: true,
        },
        children: [
          {
            path: "menu3-1-1",
            name: "Menu3-1-1",
            component: () => import("@/views/menus/menu2/level1.vue"),
            meta: {
              title: "道路网互联互通",
              icon: "api",
            },
          },
          {
            path: "menu3-1-2",
            name: "Menu3-1-2",
            component: () => import("@/views/menus/menu2/level1.vue"),
            meta: {
              title: "卫星导航和移动通讯互联互通",
              icon: "api",
            },
          },
        ],
      },
      {
        path: "menu3-2",
        name: "Menu3-2",
        redirect: "noredirect",
        meta: {
          title: "渔船搜救互联互通",
          icon: "api",
          alwaysShow: true,
        },
      },
    ],
  },

  // 一级菜单4
  {
    path: "/menu4",
    name: "Menu4",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "安全态势推演与预警",
      icon: "api",
      alwaysShow: true,
    },
    children: [
      {
        path: "menu4-1",
        name: "Menu4-1",
        redirect: "noredirect",
        meta: {
          title: "情势推演",
          icon: "api",
          alwaysShow: true,
        },
      },
      {
        path: "menu4-2",
        name: "Menu4-2",
        redirect: "noredirect",
        meta: {
          title: "情势预警",
          icon: "api",
          alwaysShow: true,
        },
      },
    ],
  },

  // 一级菜单5
  {
    path: "/menu5",
    name: "Menu5",
    component: Layout,
    redirect: "noredirect",
    meta: {
      title: "空间管控模拟与优化",
      icon: "api",
      alwaysShow: true,
    },
    children: [
      {
        path: "menu5-1",
        name: "Menu5-1",
        redirect: "noredirect",
        meta: {
          title: "应用示范情景模拟",
          icon: "api",
          alwaysShow: true,
        },
      },
      {
        path: "menu5-2",
        name: "Menu5-2",
        redirect: "noredirect",
        meta: {
          title: "空间管控智能优化",
          icon: "api",
          alwaysShow: true,
        },
      },
      {
        path: "menu5-3",
        name: "Menu5-3",
        redirect: "noredirect",
        meta: {
          title: "动态决策规划",
          icon: "api",
          alwaysShow: true,
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
      title: "测试页面",
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
