import { View, Text } from '@tarojs/components'
import { RISK_BANDS, type RiskBandKey } from '../utils/constants'

interface RiskBadgeProps {
  riskKey: RiskBandKey
  size?: 'small' | 'medium' | 'large'
  showDescription?: boolean
}

export default function RiskBadge({
  riskKey,
  size = 'medium',
  showDescription = false,
}: RiskBadgeProps) {
  const risk = RISK_BANDS[riskKey]
  if (!risk) return null

  const sizeStyles: Record<string, { fontSize: string; padding: string; iconSize: string }> = {
    small: { fontSize: 'var(--font-size-xs)', padding: '4px 12px', iconSize: '24px' },
    medium: { fontSize: 'var(--font-size-sm)', padding: '8px 20px', iconSize: '28px' },
    large: { fontSize: 'var(--font-size-md)', padding: '12px 28px', iconSize: '36px' },
  }

  const s = sizeStyles[size]

  return (
    <View>
      <View
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          backgroundColor: risk.bgColor,
          border: `2px solid ${risk.color}`,
          borderRadius: '999px',
          padding: s.padding,
        }}
      >
        <Text
          style={{
            fontSize: s.iconSize,
            color: risk.color,
            fontWeight: 'bold',
            marginRight: '8px',
            lineHeight: '1',
          }}
        >
          {risk.icon}
        </Text>
        <Text
          style={{
            fontSize: s.fontSize,
            color: risk.color,
            fontWeight: '600',
          }}
        >
          {risk.label}
        </Text>
      </View>
      {showDescription && (
        <Text
          style={{
            display: 'block',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
            marginTop: '8px',
          }}
        >
          {risk.description}
        </Text>
      )}
    </View>
  )
}
