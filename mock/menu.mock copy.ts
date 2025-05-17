import { defineMock } from "./base";

export default defineMock([
  {
    url: "menus/routes",
    method: ["GET"],
    body: {
      code: "00000",
      data: [
        // 我的页面
        {
          path: "/Database",
          component: "Layout",
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
              component: "mypages/page1",
              name: "Database",
              meta: {
                title: "数据库管理",
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
          component: "Layout",
          redirect: "noredirect",
          name: "Menu1",
          meta: {
            title: "安全态势动态监测",
            hidden: false,
            roles: ["ADMIN"],
            alwaysShow: false,
            params: null,
          },
          children: [
            {
              path: "menu1-1",
              component: "test/other_显示图标2",
              redirect: "noredirect",
              name: "Menu1-1",
              meta: {
                title: "关键要素挖掘",
                hidden: false,
                roles: ["ADMIN"],
                alwaysShow: false,
                params: null,
              },
              children: [
                {
                  path: "menu1-1-1",
                  component: "test/other_显示图标2",
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
                  component: "test/other_上传图片",
                  name: "Menu1-1-2",
                  meta: {
                    title: "多源异构数据融合",
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
              component: "test/other_显示图标2",
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
                  component: "test/other_显示图标",
                  name: "Menu1-2-1",
                  meta: {
                    title: "影像变化检测",
                    hidden: false,
                    roles: ["ADMIN"],
                    keepAlive: true,
                    alwaysShow: false,
                    params: null,
                  },
                },
                {
                  path: "menu1-2-2",
                  component: "test/other_显示图标",
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
                  component: "test/other_显示图标",
                  name: "Menu1-2-3",
                  meta: {
                    title: "异常变化检测",
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
          path: "/menu2",
          component: "Layout",
          redirect: "noredirect",
          name: "Menu2",
          meta: {
            title: "安全态势分级",
            hidden: false,
            roles: ["ADMIN"],
            alwaysShow: false,
            params: null,
          },
          children: [
            {
              path: "menu2-1",
              component: "test/other_显示图标",
              name: "Menu2-1",
              meta: {
                title: "评价模型",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "menu2-2",
              component: "test/other_显示图标2",
              name: "Menu2-2",
              meta: {
                title: "定量分级研判",
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
          path: "/menu3",
          component: "Layout",
          redirect: "noredirect",
          name: "Menu3",
          meta: {
            title: "安全态势互联互通",
            hidden: false,
            roles: ["ADMIN"],
            alwaysShow: false,
            params: null,
          },
          children: [
            {
              path: "menu3-1",
              component: "test/other_显示图标",
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
                  component: "test/other_显示图标",
                  name: "Menu3-1-1",
                  meta: {
                    title: "道路网互联互通",
                    hidden: false,
                    roles: ["ADMIN"],
                    keepAlive: true,
                    alwaysShow: false,
                    params: null,
                  },
                },
                {
                  path: "menu3-1-2",
                  component: "test/other_显示图标",
                  name: "Menu3-1-2",
                  meta: {
                    title: "卫星导航和移动通讯互联互通",
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
              component: "test/other_显示图标2",
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
          path: "/menu4",
          component: "Layout",
          redirect: "noredirect",
          name: "Menu4",
          meta: {
            title: "安全态势推演与预警",
            hidden: false,
            roles: ["ADMIN"],
            alwaysShow: false,
            params: null,
          },
          children: [
            {
              path: "menu4-1",
              component: "test/other_显示图标",
              name: "Menu4-1",
              meta: {
                title: "情势推演",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "menu4-2",
              component: "test/other_显示图标2",
              name: "Menu4-2",
              meta: {
                title: "情势预警",
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
          path: "/menu5",
          component: "Layout",
          redirect: "noredirect",
          name: "Menu5",
          meta: {
            title: "空间管控模拟与优化",
            hidden: false,
            roles: ["ADMIN"],
            alwaysShow: false,
            params: null,
          },
          children: [
            {
              path: "menu5-1",
              component: "test/other_显示图标",
              name: "Menu5-1",
              meta: {
                title: "应用示范情景模拟",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "menu5-2",
              component: "test/other_显示图标",
              name: "Menu5-2",
              meta: {
                title: "空间管控智能优化",
                hidden: false,
                roles: ["ADMIN"],
                keepAlive: true,
                alwaysShow: false,
                params: null,
              },
            },
            {
              path: "menu5-3",
              component: "test/other_显示图标2",
              name: "Menu5-3",
              meta: {
                title: "动态决策规划",
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
      msg: "一切ok",
    },
  },
]);
