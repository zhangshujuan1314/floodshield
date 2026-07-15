'use client';

import type { RiskLevel } from '@/lib/types';

interface RiskBadgeProps {
  level: RiskLevel;
  size?: 'sm' | 'md';
  showLabel?: boolean;  // Show "平台风险等级" label
}

const RISK_CONFIG: Record<RiskLevel, { label: string; icon: string; className: string }> = {
  unknown: { label: '暂无数据', icon: '❓', className: 'risk-unknown' },
  normal: { label: '正常', icon: '✅', className: 'risk-normal' },
  attention: { label: '关注', icon: '👀', className: 'risk-attention' },
  high: { label: '高危', icon: '🔶', className: 'risk-high' },
  critical: { label: '极高', icon: '🔴', className: 'risk-critical' },
};

export default function RiskBadge({ level, size = 'md', showLabel = false }: RiskBadgeProps) {
  const config = RISK_CONFIG[level] || RISK_CONFIG.unknown;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
      {showLabel && (
        <span style={{ fontSize: '12px', color: '#8c8c8c' }}>平台风险等级：</span>
      )}
      <span className={`risk-badge ${config.className} ${size === 'sm' ? 'risk-badge-sm' : ''}`}>
        <span className="risk-badge-icon">{config.icon}</span>
        <span className="risk-badge-text">{config.label}</span>
      </span>
    </span>
  );
}

export { RISK_CONFIG };
