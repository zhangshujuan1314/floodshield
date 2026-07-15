import { View, Text } from '@tarojs/components'

interface AlertCardProps {
  id: string
  level: string
  title: string
  content: string
  issuedAt: string
  source: string
}

const LEVEL_MAP: Record<string, { label: string; color: string; bgColor: string }> = {
  blue: { label: '蓝色', color: '#1890ff', bgColor: '#e6f7ff' },
  yellow: { label: '黄色', color: '#d48806', bgColor: '#fffbe6' },
  orange: { label: '橙色', color: '#d4380d', bgColor: '#fff2e8' },
  red: { label: '红色', color: '#cf1322', bgColor: '#fff1f0' },
}

export default function AlertCard({
  level,
  title,
  content,
  issuedAt,
  source,
}: AlertCardProps) {
  const levelInfo = LEVEL_MAP[level] || LEVEL_MAP.blue
  const timeStr = formatTime(issuedAt)

  return (
    <View
      style={{
        background: levelInfo.bgColor,
        border: `2px solid ${levelInfo.color}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--spacing-lg)',
        marginBottom: 'var(--spacing-md)',
      }}
    >
      {/* 头部：级别标签 + 标题 */}
      <View style={{ display: 'flex', alignItems: 'center', marginBottom: 'var(--spacing-sm)' }}>
        <View
          style={{
            background: levelInfo.color,
            color: '#ffffff',
            fontSize: 'var(--font-size-xs)',
            padding: '4px 12px',
            borderRadius: '4px',
            marginRight: 'var(--spacing-sm)',
            fontWeight: '600',
          }}
        >
          {levelInfo.label}预警
        </View>
        <Text
          style={{
            fontSize: 'var(--font-size-md)',
            fontWeight: '600',
            color: 'var(--color-text-primary)',
            flex: 1,
          }}
        >
          {title}
        </Text>
      </View>

      {/* 内容 */}
      <Text
        style={{
          fontSize: 'var(--font-size-base)',
          color: 'var(--color-text-primary)',
          lineHeight: '1.6',
          display: 'block',
          marginBottom: 'var(--spacing-sm)',
        }}
      >
        {content}
      </Text>

      {/* 来源和时间 */}
      <View style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-hint)' }}>
          来源：{source}
        </Text>
        <Text style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-hint)' }}>
          {timeStr}
        </Text>
      </View>
    </View>
  )
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr)
    const month = d.getMonth() + 1
    const day = d.getDate()
    const hour = d.getHours().toString().padStart(2, '0')
    const minute = d.getMinutes().toString().padStart(2, '0')
    return `${month}月${day}日 ${hour}:${minute}`
  } catch {
    return isoStr
  }
}
