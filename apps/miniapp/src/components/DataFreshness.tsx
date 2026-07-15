import { View, Text } from '@tarojs/components'
import { FRESHNESS_LEVELS, type FreshnessKey } from '../utils/constants'

interface DataFreshnessProps {
  freshness: FreshnessKey
  updatedAt?: string
  source?: string
}

export default function DataFreshness({ freshness, updatedAt, source }: DataFreshnessProps) {
  const level = FRESHNESS_LEVELS[freshness] || FRESHNESS_LEVELS.unknown
  const timeStr = updatedAt ? formatRelativeTime(updatedAt) : ''

  return (
    <View
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: 'var(--spacing-sm) var(--spacing-md)',
        backgroundColor: '#f9f9f9',
        borderRadius: 'var(--radius-sm)',
        marginTop: 'var(--spacing-sm)',
      }}
    >
      {/* 状态指示点 + 文字 */}
      <View
        style={{
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          backgroundColor: level.color,
          marginRight: 'var(--spacing-xs)',
        }}
      />
      <Text
        style={{
          fontSize: 'var(--font-size-xs)',
          color: level.color,
          fontWeight: '500',
          marginRight: 'var(--spacing-sm)',
        }}
      >
        {level.label}
      </Text>

      {timeStr && (
        <Text style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-hint)' }}>
          更新于 {timeStr}
        </Text>
      )}

      {source && (
        <Text
          style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-hint)',
            marginLeft: 'auto',
          }}
        >
          {source}
        </Text>
      )}
    </View>
  )
}

function formatRelativeTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMin = Math.floor(diffMs / 60000)

    if (diffMin < 1) return '刚刚'
    if (diffMin < 60) return `${diffMin}分钟前`
    const diffHour = Math.floor(diffMin / 60)
    if (diffHour < 24) return `${diffHour}小时前`
    const diffDay = Math.floor(diffHour / 24)
    return `${diffDay}天前`
  } catch {
    return ''
  }
}
