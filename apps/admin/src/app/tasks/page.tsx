'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import {
  fetchTasks, createTask, updateTaskStatus,
  dispatchNotification, fetchNotificationDelivery,
} from '@/lib/api';
import { hasPermission, getStoredUser } from '@/lib/auth';
import StatusBadge, {
  TASK_STATUS_MAP, TASK_PRIORITY_MAP, TASK_TYPE_MAP, NOTIFICATION_STATUS_MAP,
} from '@/components/StatusBadge';
import ConfirmDialog from '@/components/ConfirmDialog';
import type {
  Task, TaskType, TaskPriority, Notification, NotificationChannel,
  NotificationDelivery, User,
} from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const TASK_STEPS = ['received', 'confirmed', 'in_progress', 'feedback', 'completed'];

export default function TasksPage() {
  const { data: tasks, error, isLoading, mutate } = useSWR<Task[]>('tasks', fetchTasks);

  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<'tasks' | 'dispatch'>('tasks');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTask, setNewTask] = useState<{
    taskType: TaskType;
    title: string;
    description: string;
    assignedTo: string;
    organizationId: string;
    priority: TaskPriority;
  }>({
    taskType: 'patrol',
    priority: 'medium',
    title: '',
    description: '',
    assignedTo: '',
    organizationId: '',
  });
  const [creating, setCreating] = useState(false);

  // Dispatch form
  const [dispatchForm, setDispatchForm] = useState<{
    channel: NotificationChannel;
    recipients: string;
    message: string;
    idempotencyKey: string;
  }>({
    channel: 'push',
    recipients: '',
    message: '',
    idempotencyKey: `dispatch-${Date.now()}`,
  });
  const [confirmDispatch, setConfirmDispatch] = useState(false);
  const [dispatching, setDispatching] = useState(false);
  const [deliveryStatus, setDeliveryStatus] = useState<NotificationDelivery | null>(null);
  const [checkingDelivery, setCheckingDelivery] = useState(false);

  // Status advance confirm
  const [confirmAdvance, setConfirmAdvance] = useState<{ taskId: string; nextStatus: string } | null>(null);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) setUser(stored);
  }, []);

  const canCreateTask = user ? hasPermission(user.role, 'task:create') : false;
  const canUpdateTask = user ? hasPermission(user.role, 'task:update') : false;
  const canDispatchNotif = user ? hasPermission(user.role, 'notification:dispatch') : false;

  const handleCreateTask = async () => {
    if (!newTask.title?.trim()) return;
    setCreating(true);
    await createTask({
      taskType: newTask.taskType,
      title: newTask.title,
      description: newTask.description,
      assignedTo: newTask.assignedTo,
      organizationId: newTask.organizationId || undefined,
      priority: newTask.priority,
    });
    setCreating(false);
    setShowCreateForm(false);
    setNewTask({ taskType: 'patrol', priority: 'medium', title: '', description: '', assignedTo: '', organizationId: '' });
    mutate();
  };

  const handleAdvanceStatus = async (taskId: string, currentStatus: string) => {
    const idx = TASK_STEPS.indexOf(currentStatus);
    if (idx < 0 || idx >= TASK_STEPS.length - 1) return;
    const nextStatus = TASK_STEPS[idx + 1];
    setConfirmAdvance({ taskId, nextStatus });
  };

  const doAdvanceStatus = async () => {
    if (!confirmAdvance) return;
    await updateTaskStatus(confirmAdvance.taskId, confirmAdvance.status);
    setConfirmAdvance(null);
    mutate();
  };

  const handleDispatch = async () => {
    if (!dispatchForm.message.trim()) return;
    setDispatching(true);
    const result = await dispatchNotification({
      channel: dispatchForm.channel,
      recipients: dispatchForm.recipients.split(',').map(r => r.trim()).filter(Boolean),
      message: dispatchForm.message,
      idempotencyKey: dispatchForm.idempotencyKey,
    });
    setDispatching(false);
    setConfirmDispatch(false);
    // Check delivery
    if (result.id) {
      setCheckingDelivery(true);
      const delivery = await fetchNotificationDelivery(result.id);
      setDeliveryStatus(delivery);
      setCheckingDelivery(false);
    }
  };

  const getStepIndex = (status: string) => TASK_STEPS.indexOf(status);

  const stepLabels: Record<string, string> = {
    received: '收到',
    confirmed: '确认',
    in_progress: '处置',
    feedback: '反馈',
    completed: '完成',
  };

  const nextStepLabels: Record<string, string> = {
    received: '确认接收',
    confirmed: '开始处置',
    in_progress: '提交反馈',
    feedback: '标记完成',
  };

  return (
    <div>
      <h2 className="section-title">任务与通知</h2>

      {/* Tab 切换 */}
      <div className="filter-bar mb-md">
        <button className={`filter-btn ${activeTab === 'tasks' ? 'active' : ''}`} onClick={() => setActiveTab('tasks')}>
          📋 任务列表
        </button>
        {canDispatchNotif && (
          <button className={`filter-btn ${activeTab === 'dispatch' ? 'active' : ''}`} onClick={() => setActiveTab('dispatch')}>
            📢 通知派发
          </button>
        )}
      </div>

      {activeTab === 'tasks' && (
        <>
          <div className="flex justify-between items-center mb-md">
            <div />
            {canCreateTask && (
              <button className="btn btn-primary" onClick={() => setShowCreateForm(true)}>
                + 创建任务
              </button>
            )}
          </div>

          {isLoading ? (
            <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-text">加载中...</div></div>
          ) : error ? (
            <div className="empty-state"><div className="empty-state-icon">❌</div><div className="empty-state-text">加载失败</div></div>
          ) : (tasks || []).length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">📋</div><div className="empty-state-text">暂无任务</div></div>
          ) : (
            (tasks || []).map(task => {
              const typeConfig = TASK_TYPE_MAP[task.type] || { label: task.type, icon: '📋' };
              const stepIdx = getStepIndex(task.status);
              return (
                <div key={task.id} className="card mb-sm">
                  <div className="flex items-center justify-between mb-sm">
                    <div className="flex items-center gap-sm">
                      <span style={{ fontSize: 20 }}>{typeConfig.icon}</span>
                      <span className="font-bold">{task.title}</span>
                      <StatusBadge status={task.type} statusMap={TASK_TYPE_MAP as Record<string, { label: string; icon: string; className: string }>} />
                    </div>
                    <div className="flex items-center gap-sm">
                      <StatusBadge status={task.priority} statusMap={TASK_PRIORITY_MAP} />
                      <StatusBadge status={task.status} statusMap={TASK_STATUS_MAP} />
                    </div>
                  </div>

                  <div className="text-secondary mb-sm" style={{ fontSize: 'var(--font-size-sm)' }}>
                    {task.description}
                  </div>

                  <div className="flex items-center gap-md mb-sm text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>
                    <span>📍 {task.areaName}</span>
                    <span>👤 {task.assignedToName}</span>
                    <span>⏰ 创建于 {dayjs(task.createdAt).fromNow()}</span>
                    {task.deadline && <span>⏳ 截止 {dayjs(task.deadline).format('MM-DD HH:mm')}</span>}
                  </div>

                  {/* 进度条 */}
                  <div className="task-timeline">
                    {TASK_STEPS.map((step, i) => {
                      const stepStatus = i < stepIdx ? 'completed' : i === stepIdx ? 'active' : '';
                      return (
                        <div key={step} className={`timeline-step ${stepStatus}`}>
                          <div className="timeline-dot">
                            {i < stepIdx ? '✓' : i === stepIdx ? (i + 1) : ''}
                          </div>
                          <span className="timeline-label">{stepLabels[step]}</span>
                        </div>
                      );
                    })}
                  </div>

                  {task.feedback && (
                    <div style={{ background: '#f6ffed', padding: 'var(--spacing-sm)', borderRadius: 'var(--radius-sm)', marginTop: 'var(--spacing-sm)', fontSize: 'var(--font-size-sm)' }}>
                      💬 反馈: {task.feedback}
                    </div>
                  )}

                  {/* 操作按钮 */}
                  {canUpdateTask && stepIdx < TASK_STEPS.length - 1 && (
                    <div style={{ marginTop: 'var(--spacing-sm)' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleAdvanceStatus(task.id, task.status)}
                      >
                        推进到: {nextStepLabels[task.status] || '下一步'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </>
      )}

      {activeTab === 'dispatch' && canDispatchNotif && (
        <div className="card">
          <div className="card-title">通知派发</div>

          <div className="form-group">
            <label className="form-label">通知渠道</label>
            <select
              className="form-select"
              value={dispatchForm.channel}
              onChange={e => setDispatchForm(prev => ({ ...prev, channel: e.target.value as NotificationChannel }))}
            >
              <option value="push">📱 推送</option>
              <option value="sms">💬 短信</option>
              <option value="wechat">🟢 微信</option>
              <option value="broadcast">📻 广播</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">接收者（逗号分隔）</label>
            <input
              type="text"
              className="form-input"
              placeholder="user-001, user-002, ..."
              value={dispatchForm.recipients}
              onChange={e => setDispatchForm(prev => ({ ...prev, recipients: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label">通知内容</label>
            <textarea
              className="form-textarea"
              placeholder="通知消息内容"
              value={dispatchForm.message}
              onChange={e => setDispatchForm(prev => ({ ...prev, message: e.target.value }))}
              rows={4}
            />
          </div>

          <div className="form-group">
            <label className="form-label">幂等键（Idempotency Key）</label>
            <div className="flex gap-sm">
              <input
                type="text"
                className="form-input"
                value={dispatchForm.idempotencyKey}
                onChange={e => setDispatchForm(prev => ({ ...prev, idempotencyKey: e.target.value }))}
                style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-sm)' }}
              />
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setDispatchForm(prev => ({ ...prev, idempotencyKey: `dispatch-${Date.now()}` }))}
              >
                重新生成
              </button>
            </div>
            <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 4 }}>
              相同幂等键的重复请求将被忽略，防止重复发送
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={() => setConfirmDispatch(true)}
            disabled={!dispatchForm.message.trim()}
          >
            🚀 发送通知
          </button>

          {/* 送达状态 */}
          {checkingDelivery && (
            <div className="mt-md text-hint">正在查询送达状态...</div>
          )}
          {deliveryStatus && (
            <div className="mt-md" style={{
              background: deliveryStatus.status === 'delivered' ? '#f6ffed' : deliveryStatus.status === 'failed' ? '#fff2f0' : '#e6f7ff',
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${deliveryStatus.status === 'delivered' ? '#b7eb8f' : deliveryStatus.status === 'failed' ? '#ffa39e' : '#91caff'}`,
            }}>
              <div className="flex items-center justify-between mb-sm">
                <span className="font-bold">送达状态</span>
                <StatusBadge status={deliveryStatus.status} statusMap={NOTIFICATION_STATUS_MAP} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--spacing-sm)', fontSize: 'var(--font-size-sm)' }}>
                <div>
                  <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>总接收</div>
                  <div className="font-bold">{deliveryStatus.recipientCount}</div>
                </div>
                <div>
                  <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>已送达</div>
                  <div className="font-bold text-safe">{deliveryStatus.deliveredCount}</div>
                </div>
                <div>
                  <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>失败</div>
                  <div className="font-bold text-danger">{deliveryStatus.failedCount}</div>
                </div>
              </div>
              {deliveryStatus.completedAt && (
                <div className="text-hint" style={{ fontSize: 'var(--font-size-xs)', marginTop: 8 }}>
                  完成于 {dayjs(deliveryStatus.completedAt).format('HH:mm:ss')}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 创建任务表单 */}
      {showCreateForm && (
        <div className="dialog-overlay" onClick={() => setShowCreateForm(false)}>
          <div className="dialog-box" style={{ maxWidth: 480 }} onClick={e => e.stopPropagation()}>
            <div className="dialog-header">
              <span className="dialog-icon">📋</span>
              <h3 className="dialog-title">创建新任务</h3>
            </div>

            <div className="form-group">
              <label className="form-label">任务类型</label>
              <select
                className="form-select"
                value={newTask.taskType}
                onChange={e => setNewTask(prev => ({ ...prev, taskType: e.target.value as TaskType }))}
              >
                <option value="patrol">🔍 巡查</option>
                <option value="blockade">🚧 封控</option>
                <option value="evacuation">🚨 转移</option>
                <option value="supply_delivery">📦 物资配送</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">标题</label>
              <input
                type="text"
                className="form-input"
                placeholder="任务标题"
                value={newTask.title}
                onChange={e => setNewTask(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">描述</label>
              <textarea
                className="form-textarea"
                placeholder="任务详细描述"
                value={newTask.description}
                onChange={e => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            <div className="form-group">
              <label className="form-label">指派给（用户ID）</label>
              <input
                type="text"
                className="form-input"
                placeholder="如：u-002"
                value={newTask.assignedTo}
                onChange={e => setNewTask(prev => ({ ...prev, assignedTo: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">所属组织（可选）</label>
              <input
                type="text"
                className="form-input"
                placeholder="如：org-comm-01"
                value={newTask.organizationId}
                onChange={e => setNewTask(prev => ({ ...prev, organizationId: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">优先级</label>
              <select
                className="form-select"
                value={newTask.priority}
                onChange={e => setNewTask(prev => ({ ...prev, priority: e.target.value as TaskPriority }))}
              >
                <option value="low">⬇️ 低</option>
                <option value="medium">➡️ 中</option>
                <option value="high">⬆️ 高</option>
                <option value="urgent">🔴 紧急</option>
              </select>
            </div>

            <div className="dialog-actions">
              <button className="btn btn-secondary" onClick={() => setShowCreateForm(false)}>取消</button>
              <button className="btn btn-primary" onClick={handleCreateTask} disabled={creating || !newTask.title?.trim()}>
                {creating ? '创建中...' : '创建任务'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 推进状态确认 */}
      <ConfirmDialog
        open={!!confirmAdvance}
        title="确认推进任务状态"
        message={`将任务状态推进到「${stepLabels[confirmAdvance?.nextStatus || ''] || ''}」？`}
        confirmText="确认推进"
        variant="warning"
        onConfirm={doAdvanceStatus}
        onCancel={() => setConfirmAdvance(null)}
      />

      {/* 发送通知确认 */}
      <ConfirmDialog
        open={confirmDispatch}
        title="确认发送通知"
        message={`将通过${
          dispatchForm.channel === 'push' ? '推送' :
          dispatchForm.channel === 'sms' ? '短信' :
          dispatchForm.channel === 'wechat' ? '微信' : '广播'
        }渠道发送通知，发送后将无法撤回。`}
        confirmText="确认发送"
        variant="warning"
        onConfirm={handleDispatch}
        onCancel={() => setConfirmDispatch(false)}
      />
    </div>
  );
}
