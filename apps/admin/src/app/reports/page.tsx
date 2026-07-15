'use client';

import { useState } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchReports, verifyReport, rejectReport } from '@/lib/api';
import DataTable, { Column } from '@/components/DataTable';
import RiskBadge from '@/components/RiskBadge';
import StatusBadge, { REPORT_STATUS_MAP, REPORT_TYPE_MAP } from '@/components/StatusBadge';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { Report, ReportStatus, PaginatedData } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const STATUS_FILTERS: { key: ReportStatus | 'all'; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'pending_review', label: '待核验' },
  { key: 'verified', label: '已核验' },
  { key: 'rejected', label: '已驳回' },
  { key: 'expired', label: '已过期' },
];

export default function ReportsPage() {
  const [statusFilter, setStatusFilter] = useState<ReportStatus | 'all'>('pending_review');
  const [page, setPage] = useState(1);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'verify' | 'reject';
    reportId: string;
    reportTitle: string;
  } | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const { data, error, isLoading, mutate } = useSWR<PaginatedData<Report>>(
    ['reports', statusFilter, page],
    () => fetchReports({
      status: statusFilter === 'all' ? undefined : statusFilter,
      page,
      pageSize: 10,
    }),
    { revalidateOnFocus: false }
  );

  const handleVerify = async () => {
    if (!confirmAction) return;
    await verifyReport(confirmAction.reportId);
    setConfirmAction(null);
    mutate();
  };

  const handleReject = async () => {
    if (!confirmAction || !rejectReason.trim()) return;
    await rejectReport(confirmAction.reportId, rejectReason);
    setConfirmAction(null);
    setRejectReason('');
    mutate();
  };

  const columns: Column<Report>[] = [
    {
      key: 'priority',
      title: '优先级',
      width: '60px',
      sortable: true,
      render: (val) => {
        const v = val as number;
        const labels = ['', '低', '中低', '中', '高', '紧急'];
        const colors = ['', '#8c8c8c', '#0958d9', '#d48806', '#cf1322', '#a8071a'];
        return (
          <span style={{ color: colors[v] || '#8c8c8c', fontWeight: 600 }}>
            {v >= 4 ? '🔴' : v >= 3 ? '🟡' : '⚪'} {labels[v] || v}
          </span>
        );
      },
    },
    {
      key: 'title',
      title: '标题',
      sortable: true,
      render: (val, row) => (
        <div>
          <div className="font-bold">{String(val)}</div>
          <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>
            {(REPORT_TYPE_MAP[row.type] as { label: string })?.label || row.type}
          </div>
        </div>
      ),
    },
    {
      key: 'riskLevel',
      title: '风险',
      width: '80px',
      render: (val) => <RiskBadge level={val as 'normal' | 'attention' | 'high' | 'critical'} size="sm" />,
    },
    {
      key: 'status',
      title: '状态',
      width: '90px',
      render: (val) => <StatusBadge status={val as string} statusMap={REPORT_STATUS_MAP} />,
    },
    {
      key: 'reporterName',
      title: '报告人',
      width: '80px',
    },
    {
      key: 'location',
      title: '位置',
      render: (val) => {
        const loc = val as Report['location'];
        return <span className="text-secondary">{loc.address}</span>;
      },
    },
    {
      key: 'credibilityScore',
      title: '可信度',
      width: '70px',
      sortable: true,
      render: (val) => {
        const score = val as number;
        const color = score >= 0.8 ? 'var(--color-safe)' : score >= 0.5 ? 'var(--color-warning)' : 'var(--color-danger)';
        return <span style={{ color, fontWeight: 600 }}>{Math.round(score * 100)}%</span>;
      },
    },
    {
      key: 'createdAt',
      title: '时间',
      width: '90px',
      sortable: true,
      render: (val) => (
        <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>
          {dayjs(val as string).fromNow()}
        </span>
      ),
    },
    {
      key: 'id',
      title: '操作',
      width: '140px',
      render: (_val, row) => (
        <div className="flex gap-sm">
          <a href={`/reports/${row.id}`} className="btn btn-secondary btn-sm">
            详情
          </a>
          {row.status === 'pending_review' && (
            <>
              <button
                className="btn btn-success btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setConfirmAction({ type: 'verify', reportId: row.id, reportTitle: row.title });
                }}
              >
                核验
              </button>
              <button
                className="btn btn-danger btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setConfirmAction({ type: 'reject', reportId: row.id, reportTitle: row.title });
                }}
              >
                驳回
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <h2 className="section-title">报告队列</h2>

      {/* 筛选栏 */}
      <div className="filter-bar">
        {STATUS_FILTERS.map(f => (
          <button
            key={f.key}
            className={`filter-btn ${statusFilter === f.key ? 'active' : ''}`}
            onClick={() => { setStatusFilter(f.key); setPage(1); }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* 表格 */}
      {isLoading ? (
        <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-text">加载中...</div></div>
      ) : error ? (
        <div className="empty-state"><div className="empty-state-icon">❌</div><div className="empty-state-text">加载失败</div></div>
      ) : (
        <DataTable
          columns={columns}
          data={data?.items || []}
          rowKey="id"
          pageSize={10}
          emptyText="暂无报告"
        />
      )}

      {/* 核验确认对话框 */}
      <ConfirmDialog
        open={confirmAction?.type === 'verify'}
        title="确认核验报告"
        message={`确定要核验通过报告「${confirmAction?.reportTitle}」吗？核验后该报告将标记为已确认。`}
        confirmText="确认核验"
        variant="default"
        onConfirm={handleVerify}
        onCancel={() => setConfirmAction(null)}
      />

      {/* 驳回对话框 */}
      {confirmAction?.type === 'reject' && (
        <div className="dialog-overlay" onClick={() => setConfirmAction(null)}>
          <div className="dialog-box dialog-danger" onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <span className="dialog-icon">⚠️</span>
              <h3 className="dialog-title">驳回报告</h3>
            </div>
            <p className="dialog-message">
              确定要驳回报告「{confirmAction.reportTitle}」吗？请填写驳回原因。
            </p>
            <div className="form-group">
              <textarea
                className="form-textarea"
                placeholder="请输入驳回原因（必填）"
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                rows={3}
              />
            </div>
            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={() => { setConfirmAction(null); setRejectReason(''); }}>
                取消
              </button>
              <button
                className="btn btn-danger"
                disabled={!rejectReason.trim()}
                onClick={handleReject}
              >
                确认驳回
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
