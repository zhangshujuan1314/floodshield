import { View, Text } from '@tarojs/components'

interface ErrorStateProps {
  icon?: string
  title?: string
  message: string
  retryText?: string
  onRetry?: () => void
}

export default function ErrorState({
  icon = '⚠️',
  title = '加载失败',
  message,
  retryText = '重试',
  onRetry,
}: ErrorStateProps) {
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
      <Text style={{ fontSize: '80px', marginBottom: 'var(--spacing-lg)' }}>{icon}</Text>
      <Text
        style={{
          fontSize: 'var(--font-size-md)',
          color: 'var(--color-text-primary)',
          fontWeight: '600',
          marginBottom: 'var(--spacing-sm)',
        }}
      >
        {title}
      </Text>
      <Text
        style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-hint)',
          textAlign: 'center',
          lineHeight: '1.5',
          marginBottom: 'var(--spacing-lg)',
        }}
      >
        {message}
      </Text>
      {onRetry && (
        <View
          style={{
            padding: 'var(--spacing-sm) var(--spacing-xl)',
            backgroundColor: 'var(--color-primary)',
            borderRadius: '999px',
          }}
          onClick={onRetry}
        >
          <Text style={{ fontSize: 'var(--font-size-base)', color: '#ffffff' }}>{retryText}</Text>
        </View>
      )}
    </View>
  )
}
