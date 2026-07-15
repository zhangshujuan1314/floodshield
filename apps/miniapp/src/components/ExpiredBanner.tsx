import { View, Text } from '@tarojs/components'

interface ExpiredBannerProps {
  expiresAt: string
  onRefresh?: () => void
}

export default function ExpiredBanner({ expiresAt, onRefresh }: ExpiredBannerProps) {
  const isExpired = checkExpired(expiresAt)
  const expiredTimeStr = isExpired ? formatExpiredTime(expiresAt) : ''

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
        <View>
          <Text
            style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-warning)',
              fontWeight: '500',
              display: 'block',
            }}
          >
            信息已过期，请刷新获取最新数据
          </Text>
          {expiredTimeStr && (
            <Text
              style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-hint)',
                display: 'block',
              }}
            >
              过期时间：{expiredTimeStr}
            </Text>
          )}
        </View>
      </View>
      {onRefresh && (
        <View
          style={{
            padding: '8px 20px',
            backgroundColor: 'var(--color-warning)',
            borderRadius: '999px',
            marginLeft: 'var(--spacing-sm)',
            flexShrink: 0,
          }}
          onClick={onRefresh}
        >
          <Text style={{ fontSize: 'var(--font-size-xs)', color: '#ffffff', fontWeight: '600' }}>刷新</Text>
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

function formatExpiredTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    const hour = d.getHours().toString().padStart(2, '0')
    const minute = d.getMinutes().toString().padStart(2, '0')
    return `${hour}:${minute}`
  } catch {
    return ''
  }
}
