import { useLaunch } from '@tarojs/taro'
import { PropsWithChildren } from 'react'
import './app.scss'

function App({ children }: PropsWithChildren) {
  useLaunch(() => {
    console.log('汛安 App 启动')
  })

  return children
}

export default App
