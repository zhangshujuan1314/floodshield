import { useLaunch } from '@tarojs/taro'
import Taro from '@tarojs/taro'
import { PropsWithChildren } from 'react'
import './app.scss'

function App({ children }: PropsWithChildren) {
  useLaunch(() => {
    console.log('汛安 App 启动')

    // 加载用户设置并应用
    try {
      const settings = Taro.getStorageSync('user_settings')
      if (settings) {
        applySettings(settings)
      }
    } catch {
      // 静默
    }

    // 监听网络状态变化
    Taro.onNetworkStatusChange((res) => {
      if (res.isConnected) {
        console.log('网络已恢复')
        // 网络恢复时触发数据刷新（通过事件总线或页面自行监听）
        Taro.showToast({ title: '网络已恢复', icon: 'success', duration: 1500 })
      } else {
        console.log('网络已断开')
        Taro.showToast({ title: '网络已断开，显示缓存数据', icon: 'none', duration: 2000 })
      }
    })
  })

  return children
}

function applySettings(settings: Record<string, unknown>) {
  // 在小程序环境中，通过页面 class 应用设置
  // Taro 的页面元素在运行时才能访问
  // 此处存储设置，各页面在渲染时读取
  if (settings.fontSize === 'large' || settings.fontSize === 'xlarge') {
    // 字号设置已保存在 storage 中，页面通过 CSS 变量读取
  }
  if (settings.highContrast) {
    // 高对比设置已保存在 storage 中
  }
}

export default App
