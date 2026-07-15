import { useState, useCallback } from 'react'
import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'

interface VoiceButtonProps {
  text: string
  size?: 'small' | 'medium' | 'large'
}

export default function VoiceButton({ text, size = 'medium' }: VoiceButtonProps) {
  const [playing, setPlaying] = useState(false)

  const sizeMap = {
    small: { btn: '48px', icon: '24px' },
    medium: { btn: '64px', icon: '32px' },
    large: { btn: '80px', icon: '40px' },
  }
  const s = sizeMap[size]

  const handlePlay = useCallback(async () => {
    if (playing) return

    // 检查语音播报能力
    const plugin = Taro.requirePlugin?.('wx-tts-speech') ?? null
    if (!plugin) {
      Taro.showToast({ title: '语音功能暂不可用', icon: 'none' })
      return
    }

    setPlaying(true)
    try {
      const innerAudioContext = Taro.createInnerAudioContext()
      // 实际接入 TTS 服务时替换为真实 URL
      innerAudioContext.src = ''
      innerAudioContext.onEnded(() => setPlaying(false))
      innerAudioContext.onError(() => {
        setPlaying(false)
        Taro.showToast({ title: '语音播放失败', icon: 'none' })
      })
    } catch {
      setPlaying(false)
      Taro.showToast({ title: '语音播放失败', icon: 'none' })
    }
  }, [playing, text])

  return (
    <View
      style={{
        width: s.btn,
        height: s.btn,
        borderRadius: '50%',
        backgroundColor: playing ? 'var(--color-primary)' : 'var(--color-primary-light)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '2px solid var(--color-primary)',
      }}
      onClick={handlePlay}
    >
      <Text
        style={{
          fontSize: s.icon,
          color: playing ? '#ffffff' : 'var(--color-primary)',
          fontWeight: 'bold',
        }}
      >
        {playing ? '⏸' : '🔊'}
      </Text>
    </View>
  )
}
