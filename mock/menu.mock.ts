import { defineMock } from "./base";

export default defineMock([
  {
    url: "menus/routes",
    method: ["GET"],
    body: {
      code: "00000",
      data: [
        /*
        // 我的页面
        {
          path: "/mypages",
          component: "Layout",
          redirect: "noredirect",
          name: "mypages",
          meta: {
            title: "我的页面",
            hidden: false,
            roles: ["ADMIN"],
            alwaysShow: false,
            params: null,
          },
          children: [
            {
              path: "page1",
              component: "mypages/page1",
              name: "page1",
              meta: {
                title: "页面1",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "page2",
              component: "mypages/page2",
              name: "page2",
              meta: {
                title: "页面2",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "page3",
              component: "mypages/page3",
              name: "page3",
              meta: {
                title: "页面3",
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
          path: "/test",
          component: "Layout",
          redirect: "noredirect",
          name: "test",
          meta: {
            title: "测试页面",
            hidden: false,
            roles: ["ADMIN"],
            alwaysShow: false,
            params: null,
          },
          children: [
            {
              path: "test1",
              component: "test/other_显示图标",
              name: "test1",
              meta: {
                title: "显示图标1",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "test2",
              component: "test/other_显示图标2",
              name: "test2",
              meta: {
                title: "显示图标2",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "test3",
              component: "test/other_上传图片",
              name: "test3",
              meta: {
                title: "上传图片",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "test4",
              component: "test/cecium_加载本地wms服务",
              name: "test4",
              meta: {
                title: "加载本地wms服务",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "test5",
              component: "test/index copy",
              name: "test5",
              meta: {
                title: "模板页面",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
          ],
        },
        */
      ],
      msg: "一切ok",
    },
  },
]);
