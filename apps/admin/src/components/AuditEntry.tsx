'use client';

import dayjs from 'dayjs';
import type { AuditLog } from '@/lib/types';

interface AuditEntryProps {
  entry: AuditLog;
  onViewDetail?: (entry: AuditLog) => void;
}

export default function AuditEntry({ entry, onViewDetail }: AuditEntryProps) {
  const roleLabel: Record<string, string> = {
    admin: '管理员',
    community: '社区',
    emergency_station: '应急站',
  };

  return (
    <div className="audit-entry">
      <div className="audit-entry-header">
        <span className="audit-entry-action">{entry.action}</span>
        <span className="audit-entry-time">
          {dayjs(entry.timestamp).format('MM-DD HH:mm:ss')}
        </span>
      </div>
      <div className="audit-entry-body">
        <span className="audit-entry-actor">
          {entry.actor}
          <span className={`role-badge role-${entry.actorRole}`}>
            {roleLabel[entry.actorRole] || entry.actorRole}
          </span>
        </span>
        <span className="audit-entry-resource">
          {entry.resource}/{entry.resourceId}
        </span>
      </div>
      {entry.detail && (
        <div className="audit-entry-detail">{entry.detail}</div>
      )}
      <div className="audit-entry-footer">
        <span className="audit-entry-meta">请求ID: {entry.requestId}</span>
        <span className="audit-entry-meta">IP: {entry.ip}</span>
        {onViewDetail && (
          <button className="btn-link" onClick={() => onViewDetail(entry)}>
            查看详情
          </button>
        )}
      </div>
    </div>
  );
}
