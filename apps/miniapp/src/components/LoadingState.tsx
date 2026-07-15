import { View, Text } from '@tarojs/components'

interface LoadingStateProps {
  text?: string
}

export default function LoadingState({ text = '加载中...' }: LoadingStateProps) {
  return (
    <View
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--spacing-xl) var(--spacing-lg)',
      }}
    >
      <View
        style={{
          width: '48px',
          height: '48px',
          border: '4px solid var(--color-border)',
          borderTopColor: 'var(--color-primary)',
          borderRadius: '50%',
          marginBottom: 'var(--spacing-lg)',
          animation: 'spin 1s linear infinite',
        }}
      />
      <Text
        style={{
          fontSize: 'var(--font-size-base)',
          color: 'var(--color-text-hint)',
        }}
      >
        {text}
      </Text>
    </View>
  )
}
