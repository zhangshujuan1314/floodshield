import { View, Text } from '@tarojs/components'

interface ExpiredBannerProps {
  expiresAt: string
  onRefresh?: () => void
}

export default function ExpiredBanner({ expiresAt, onRefresh }: ExpiredBannerProps) {
  const isExpired = checkExpired(expiresAt)

  if (!isExpired) return null

  return (
    <View
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--spacing-sm) var(--spacing-md)',
        backgroundColor: 'var(--color-warning-light)',
        border: '2px solid var(--color-warning)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: 'var(--spacing-md)',
      }}
    >
      <View style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
        <Text
          style={{
            fontSize: 'var(--font-size-lg)',
            color: 'var(--color-warning)',
            marginRight: 'var(--spacing-sm)',
          }}
        >
          ⏰
        </Text>
        <Text
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-warning)',
            fontWeight: '500',
          }}
        >
          信息已过期，可能存在变化，请刷新获取最新数据
        </Text>
      </View>
      {onRefresh && (
        <View
          style={{
            padding: '6px 16px',
            backgroundColor: 'var(--color-warning)',
            borderRadius: '999px',
            marginLeft: 'var(--spacing-sm)',
            flexShrink: 0,
          }}
          onClick={onRefresh}
        >
          <Text style={{ fontSize: 'var(--font-size-xs)', color: '#ffffff' }}>刷新</Text>
        </View>
      )}
    </View>
  )
}

function checkExpired(expiresAt: string): boolean {
  try {
    return new Date(expiresAt).getTime() < Date.now()
  } catch {
    return false
  }
}
