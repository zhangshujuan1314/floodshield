'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchReports, verifyReport, rejectReport } from '@/lib/api';
import { hasPermission, getStoredUser } from '@/lib/auth';
import DataTable, { Column } from '@/components/DataTable';
import RiskBadge from '@/components/RiskBadge';
import StatusBadge, { REPORT_STATUS_MAP, REPORT_TYPE_MAP } from '@/components/StatusBadge';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { Report, ReportStatus, PaginatedData, User } from '@/lib/types';

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
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<ReportStatus | 'all'>('pending_review');
  const [page, setPage] = useState(1);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'verify' | 'reject';
    reportId: string;
    reportTitle: string;
  } | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) setUser(stored);
  }, []);

  const canVerify = user ? hasPermission(user.role, 'report:verify') : false;
  const canReject = user ? hasPermission(user.role, 'report:reject') : false;

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
      key: 'id',
      title: 'ID',
      width: '90px',
      render: (val) => (
        <span style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>
          {String(val).slice(0, 10)}
        </span>
      ),
    },
    {
      key: 'type',
      title: '类型',
      width: '80px',
      render: (val) => {
        const cfg = REPORT_TYPE_MAP[val as string] || { label: String(val), icon: '📌' };
        return <span>{cfg.icon} {cfg.label}</span>;
      },
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
      key: 'status',
      title: '状态',
      width: '90px',
      sortable: true,
      render: (val) => <StatusBadge status={val as string} statusMap={REPORT_STATUS_MAP} />,
    },
    {
      key: 'priority',
      title: '优先级',
      width: '70px',
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
      key: 'createdAt',
      title: '提交时间',
      width: '110px',
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
      width: '180px',
      render: (_val, row) => (
        <div className="flex gap-sm">
          <button
            className="btn btn-secondary btn-sm"
            onClick={(e) => { e.stopPropagation(); router.push(`/reports/${row.id}`); }}
          >
            详情
          </button>
          {row.status === 'pending_review' && canVerify && (
            <button
              className="btn btn-success btn-sm"
              onClick={(e) => {
                e.stopPropagation();
                setConfirmAction({ type: 'verify', reportId: row.id, reportTitle: row.title });
              }}
            >
              核验
            </button>
          )}
          {row.status === 'pending_review' && canReject && (
            <button
              className="btn btn-danger btn-sm"
              onClick={(e) => {
                e.stopPropagation();
                setConfirmAction({ type: 'reject', reportId: row.id, reportTitle: row.title });
              }}
            >
              驳回
            </button>
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
      ) : (data?.items || []).length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">📋</div><div className="empty-state-text">暂无报告</div></div>
      ) : (
        <>
          <DataTable
            columns={columns}
            data={data?.items || []}
            rowKey="id"
            pageSize={10}
            emptyText="暂无报告"
            onRowClick={(row) => router.push(`/reports/${row.id}`)}
          />
          {/* 服务端分页 */}
          {data && data.totalPages > 1 && (
            <div className="flex items-center justify-between mt-md">
              <span className="text-hint" style={{ fontSize: 'var(--font-size-sm)' }}>
                共 {data.total} 条，第 {data.page}/{data.totalPages} 页
              </span>
              <div className="flex gap-sm">
                <button
                  className="pagination-btn"
                  disabled={page <= 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  上一页
                </button>
                <button
                  className="pagination-btn"
                  disabled={page >= data.totalPages}
                  onClick={() => setPage(p => p + 1)}
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
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
