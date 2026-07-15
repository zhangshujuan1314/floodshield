import { View, Text } from '@tarojs/components'

interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  actionText?: string
  onAction?: () => void
}

export default function EmptyState({
  icon = '📭',
  title,
  description,
  actionText,
  onAction,
}: EmptyStateProps) {
  return (
    <View
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--spacing-xl) var(--spacing-lg)',
        minHeight: '240px',
      }}
    >
      <Text style={{ fontSize: '64px', marginBottom: 'var(--spacing-md)' }}>{icon}</Text>
      <Text
        style={{
          fontSize: 'var(--font-size-md)',
          color: 'var(--color-text-primary)',
          fontWeight: '500',
          marginBottom: 'var(--spacing-xs)',
        }}
      >
        {title}
      </Text>
      {description && (
        <Text
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-hint)',
            textAlign: 'center',
            lineHeight: '1.6',
            maxWidth: '480px',
          }}
        >
          {description}
        </Text>
      )}
      {actionText && onAction && (
        <View
          style={{
            marginTop: 'var(--spacing-lg)',
            padding: 'var(--spacing-sm) var(--spacing-lg)',
            backgroundColor: 'var(--color-primary)',
            borderRadius: '999px',
          }}
          onClick={onAction}
        >
          <Text style={{ fontSize: 'var(--font-size-base)', color: '#ffffff' }}>{actionText}</Text>
        </View>
      )}
    </View>
  )
}
