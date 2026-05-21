import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'Odometer' },
      },
      {
        path: 'opportunity',
        name: 'Opportunity',
        meta: { title: '商机登记', icon: 'Aim' },
        redirect: '/opportunity/list',
        children: [
          {
            path: 'list',
            name: 'OpportunityList',
            component: () => import('@/views/opportunity/List.vue'),
            meta: { title: '商机列表' },
          },
          {
            path: 'create',
            name: 'OpportunityCreate',
            component: () => import('@/views/opportunity/Form.vue'),
            meta: { title: '新建商机', hideInMenu: true, activeMenu: '/opportunity/list' },
          },
          {
            path: 'edit/:id',
            name: 'OpportunityEdit',
            component: () => import('@/views/opportunity/Form.vue'),
            meta: { title: '编辑商机', hideInMenu: true, activeMenu: '/opportunity/list' },
          },
          {
            path: 'detail/:id',
            name: 'OpportunityDetail',
            component: () => import('@/views/opportunity/Detail.vue'),
            meta: { title: '商机详情', hideInMenu: true, activeMenu: '/opportunity/list' },
          },
        ],
      },
      {
        path: 'bidding',
        name: 'Bidding',
        meta: { title: '招投标', icon: 'Notification' },
        redirect: '/bidding/list',
        children: [
          {
            path: 'list',
            name: 'BiddingList',
            component: () => import('@/views/bidding/List.vue'),
            meta: { title: '招投标管理' },
          },
          {
            path: 'library',
            name: 'BiddingLibrary',
            component: () => import('@/views/bidding/Library.vue'),
            meta: { title: '招投标范本库' },
          },
          {
            path: 'detail/:id',
            name: 'BiddingDetail',
            component: () => import('@/views/bidding/Detail.vue'),
            meta: { title: '招投标详情', hideInMenu: true, activeMenu: '/bidding/list' },
          },
        ],
      },
      {
        path: 'contract',
        name: 'Contract',
        meta: { title: '合同管理', icon: 'Document' },
        redirect: '/contract/list',
        children: [
          {
            path: 'list',
            name: 'ContractList',
            component: () => import('@/views/contract/List.vue'),
            meta: { title: '合同列表' },
          },
          {
            path: 'create',
            name: 'ContractCreate',
            component: () => import('@/views/contract/Form.vue'),
            meta: { title: '发起合同', hideInMenu: true, activeMenu: '/contract/list' },
          },
          {
            path: 'detail/:id',
            name: 'ContractDetail',
            component: () => import('@/views/contract/Detail.vue'),
            meta: { title: '合同详情', hideInMenu: true, activeMenu: '/contract/list' },
          },
        ],
      },
      {
        path: 'project',
        name: 'Project',
        meta: { title: '项目立项', icon: 'OfficeBuilding' },
        redirect: '/project/list',
        children: [
          {
            path: 'list',
            name: 'ProjectList',
            component: () => import('@/views/project/List.vue'),
            meta: { title: '立项列表' },
          },
          {
            path: 'create',
            name: 'ProjectCreate',
            component: () => import('@/views/project/Form.vue'),
            meta: { title: '新建立项', hideInMenu: true, activeMenu: '/project/list' },
          },
          {
            path: 'detail/:id',
            name: 'ProjectDetail',
            component: () => import('@/views/project/Detail.vue'),
            meta: { title: '立项详情', hideInMenu: true, activeMenu: '/project/list' },
          },
        ],
      },
      {
        path: 'department',
        name: 'Department',
        meta: { title: '部门项目', icon: 'Files' },
        redirect: '/department/list',
        children: [
          {
            path: 'list',
            name: 'DepartmentList',
            component: () => import('@/views/department/List.vue'),
            meta: { title: '部门任务' },
          },
          {
            path: 'detail/:id',
            name: 'DepartmentDetail',
            component: () => import('@/views/department/Detail.vue'),
            meta: { title: '任务详情', hideInMenu: true, activeMenu: '/department/list' },
          },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.afterEach((to) => {
  const title = to.meta?.title
  if (title) document.title = `${title} - 项目管理 ERP`
})

export default router
