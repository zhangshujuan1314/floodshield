'use client';

import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import type { DataStatus } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

interface DataFreshnessProps {
  statuses: DataStatus[];
}

const STATUS_CONFIG: Record<string, { icon: string; className: string }> = {
  fresh: { icon: '🟢', className: 'freshness-fresh' },
  stale: { icon: '🟡', className: 'freshness-stale' },
  offline: { icon: '🔴', className: 'freshness-offline' },
};

export default function DataFreshness({ statuses }: DataFreshnessProps) {
  return (
    <div className="data-freshness">
      <h3 className="section-subtitle">数据源状态</h3>
      <div className="freshness-grid">
        {statuses.map((status) => {
          const config = STATUS_CONFIG[status.status] || STATUS_CONFIG.offline;
          return (
            <div key={status.source} className={`freshness-item ${config.className}`}>
              <span className="freshness-icon">{config.icon}</span>
              <span className="freshness-name">{status.source}</span>
              <span className="freshness-time">
                {dayjs(status.lastUpdated).fromNow()}
              </span>
              {status.isStale && status.staleDuration && (
                <span className="freshness-warning">
                  数据滞后 {status.staleDuration} 分钟
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
