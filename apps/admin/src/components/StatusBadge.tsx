'use client';

interface StatusBadgeProps {
  status: string;
  statusMap: Record<string, { label: string; icon: string; className: string }>;
}

export default function StatusBadge({ status, statusMap }: StatusBadgeProps) {
  const config = statusMap[status] || { label: status, icon: '❓', className: 'status-unknown' };
  return (
    <span className={`status-badge ${config.className}`}>
      <span className="status-badge-icon">{config.icon}</span>
      <span className="status-badge-text">{config.label}</span>
    </span>
  );
}

// 预定义状态映射
export const REPORT_STATUS_MAP: Record<string, { label: string; icon: string; className: string }> = {
  pending_review: { label: '待核验', icon: '⏳', className: 'status-pending' },
  verified: { label: '已核验', icon: '✅', className: 'status-verified' },
  rejected: { label: '已驳回', icon: '❌', className: 'status-rejected' },
  expired: { label: '已过期', icon: '⏰', className: 'status-expired' },
};

export const SHELTER_STATUS_MAP: Record<string, { label: string; icon: string; className: string }> = {
  open: { label: '开放', icon: '🟢', className: 'status-open' },
  full: { label: '满员', icon: '🟡', className: 'status-full' },
  closed: { label: '关闭', icon: '⚪', className: 'status-closed' },
  maintenance: { label: '维护中', icon: '🔧', className: 'status-maintenance' },
};

export const TASK_STATUS_MAP: Record<string, { label: string; icon: string; className: string }> = {
  received: { label: '已收到', icon: '📥', className: 'status-pending' },
  confirmed: { label: '已确认', icon: '✔️', className: 'status-confirmed' },
  in_progress: { label: '处置中', icon: '🔄', className: 'status-in-progress' },
  feedback: { label: '已反馈', icon: '💬', className: 'status-feedback' },
  completed: { label: '已完成', icon: '✅', className: 'status-completed' },
};

export const NOTIFICATION_STATUS_MAP: Record<string, { label: string; icon: string; className: string }> = {
  pending: { label: '待发送', icon: '⏳', className: 'status-pending' },
  sent: { label: '已发送', icon: '📤', className: 'status-sent' },
  delivered: { label: '已送达', icon: '✅', className: 'status-delivered' },
  failed: { label: '发送失败', icon: '❌', className: 'status-failed' },
};

export const TASK_PRIORITY_MAP: Record<string, { label: string; icon: string; className: string }> = {
  low: { label: '低', icon: '⬇️', className: 'priority-low' },
  medium: { label: '中', icon: '➡️', className: 'priority-medium' },
  high: { label: '高', icon: '⬆️', className: 'priority-high' },
  urgent: { label: '紧急', icon: '🔴', className: 'priority-urgent' },
};

export const TASK_TYPE_MAP: Record<string, { label: string; icon: string }> = {
  patrol: { label: '巡查', icon: '🔍' },
  blockade: { label: '封控', icon: '🚧' },
  evacuation: { label: '转移', icon: '🚨' },
  supply_delivery: { label: '物资配送', icon: '📦' },
};

export const ROAD_SEVERITY_MAP: Record<string, { label: string; icon: string; className: string }> = {
  passable: { label: '可通行', icon: '🟢', className: 'severity-passable' },
  difficult: { label: '通行困难', icon: '🟡', className: 'severity-difficult' },
  blocked: { label: '断路', icon: '🔴', className: 'severity-blocked' },
};

export const REPORT_TYPE_MAP: Record<string, { label: string; icon: string }> = {
  waterlogging: { label: '积水', icon: '🌊' },
  road_blocked: { label: '道路阻断', icon: '🚧' },
  shelter_need: { label: '需要安置', icon: '🏠' },
  rescue_request: { label: '求救', icon: '🆘' },
  other: { label: '其他', icon: '📌' },
};
