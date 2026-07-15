export default defineAppConfig({
  pages: [
    'pages/index/index',
    'pages/map/index',
    'pages/report/index',
    'pages/shelters/index',
    'pages/route/index',
    'pages/profile/index',
  ],
  window: {
    backgroundTextStyle: 'light',
    navigationBarBackgroundColor: '#1890ff',
    navigationBarTitleText: '汛安',
    navigationBarTextStyle: 'white',
  },
  tabBar: {
    color: '#999999',
    selectedColor: '#1890ff',
    backgroundColor: '#ffffff',
    borderStyle: 'black',
    list: [
      {
        pagePath: 'pages/index/index',
        text: '首页',
        iconPath: 'assets/tab/home.png',
        selectedIconPath: 'assets/tab/home-active.png',
      },
      {
        pagePath: 'pages/map/index',
        text: '地图',
        iconPath: 'assets/tab/map.png',
        selectedIconPath: 'assets/tab/map-active.png',
      },
      {
        pagePath: 'pages/shelters/index',
        text: '避险',
        iconPath: 'assets/tab/shelter.png',
        selectedIconPath: 'assets/tab/shelter-active.png',
      },
      {
        pagePath: 'pages/profile/index',
        text: '我的',
        iconPath: 'assets/tab/profile.png',
        selectedIconPath: 'assets/tab/profile-active.png',
      },
    ],
  },
})
