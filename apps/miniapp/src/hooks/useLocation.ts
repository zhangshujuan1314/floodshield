import { useState, useEffect, useCallback } from 'react'
import Taro from '@tarojs/taro'

interface LocationState {
  latitude: number | null
  longitude: number | null
  address: string
  loading: boolean
  error: string | null
  permissionDenied: boolean
}

export function useLocation() {
  const [state, setState] = useState<LocationState>({
    latitude: null,
    longitude: null,
    address: '',
    loading: true,
    error: null,
    permissionDenied: false,
  })

  const requestLocation = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      // 先检查授权状态
      const authRes = await Taro.getSetting()
      if (authRes.authSetting['scope.userLocation'] === false) {
        // 用户曾拒绝，引导去设置页
        setState({
          latitude: null,
          longitude: null,
          address: '',
          loading: false,
          error: '需要位置权限才能获取附近风险信息',
          permissionDenied: true,
        })
        return
      }

      const res = await Taro.getLocation({
        type: 'gcj02',
        isHighAccuracy: true,
        highAccuracyExpireTime: 30000,
      })

      // 尝试逆地理编码
      let address = ''
      try {
        const geocoder = await Taro.request({
          url: `https://apis.map.qq.com/ws/geocoder/v1/?location=${res.latitude},${res.longitude}&key=placeholder`,
          method: 'GET',
        })
        address = (geocoder.data as any)?.result?.formatted_address || ''
      } catch {
        // 逆地理编码失败不影响主流程
      }

      setState({
        latitude: res.latitude,
        longitude: res.longitude,
        address,
        loading: false,
        error: null,
        permissionDenied: false,
      })
    } catch (err) {
      const isPermissionError =
        err instanceof Error && err.message.includes('auth')

      setState({
        latitude: null,
        longitude: null,
        address: '',
        loading: false,
        error: isPermissionError
          ? '需要位置权限才能获取附近风险信息'
          : '获取位置失败，请检查定位是否开启',
        permissionDenied: isPermissionError,
      })
    }
  }, [])

  const openSetting = useCallback(async () => {
    try {
      await Taro.openSetting()
      // 从设置页返回后重新获取位置
      requestLocation()
    } catch {
      // 用户取消设置页
    }
  }, [requestLocation])

  useEffect(() => {
    requestLocation()
  }, [requestLocation])

  return {
    ...state,
    requestLocation,
    openSetting,
  }
}
