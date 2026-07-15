'use client';

import { useState } from 'react';
import useSWR from 'swr';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { fetchTasks, fetchNotifications, createTask, updateTaskStatus, dispatchNotification } from '@/lib/api';
import StatusBadge, {
  TASK_STATUS_MAP, TASK_PRIORITY_MAP, TASK_TYPE_MAP, NOTIFICATION_STATUS_MAP,
} from '@/components/StatusBadge';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { Task, TaskType, TaskPriority, Notification } from '@/lib/types';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const TASK_STEPS = ['received', 'confirmed', 'in_progress', 'feedback', 'completed'];

export default function TasksPage() {
  const { data: tasks, error, isLoading, mutate } = useSWR<Task[]>('tasks', fetchTasks);
  const { data: notifications, mutate: mutateNotifs } = useSWR<Notification[]>('notifications', fetchNotifications);

  const [activeTab, setActiveTab] = useState<'tasks' | 'notifications'>('tasks');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTask, setNewTask] = useState<Partial<Task>>({
    type: 'patrol',
    priority: 'medium',
    title: '',
    description: '',
    areaName: '',
    deadline: '',
  });
  const [confirmDispatch, setConfirmDispatch] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const handleCreateTask = async () => {
    if (!newTask.title?.trim()) return;
    setCreating(true);
    await createTask(newTask);
    setCreating(false);
    setShowCreateForm(false);
    setNewTask({ type: 'patrol', priority: 'medium', title: '', description: '', areaName: '', deadline: '' });
    mutate();
  };

  const handleAdvanceStatus = async (taskId: string, currentStatus: string) => {
    const idx = TASK_STEPS.indexOf(currentStatus);
    if (idx < 0 || idx >= TASK_STEPS.length - 1) return;
    const nextStatus = TASK_STEPS[idx + 1];
    await updateTaskStatus(taskId, nextStatus);
    mutate();
  };

  const handleDispatch = async () => {
    if (!confirmDispatch) return;
    await dispatchNotification(confirmDispatch);
    setConfirmDispatch(null);
    mutateNotifs();
  };

  const getStepIndex = (status: string) => TASK_STEPS.indexOf(status);

  return (
    <div>
      <h2 className="section-title">任务与通知</h2>

      {/* Tab 切换 */}
      <div className="filter-bar mb-md">
        <button className={`filter-btn ${activeTab === 'tasks' ? 'active' : ''}`} onClick={() => setActiveTab('tasks')}>
          📋 任务列表
        </button>
        <button className={`filter-btn ${activeTab === 'notifications' ? 'active' : ''}`} onClick={() => setActiveTab('notifications')}>
          📢 通知
        </button>
      </div>

      {activeTab === 'tasks' && (
        <>
          <div className="flex justify-between items-center mb-md">
            <div />
            <button className="btn btn-primary" onClick={() => setShowCreateForm(true)}>
              ➕ 创建任务
            </button>
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
                      const stepLabels: Record<string, string> = {
                        received: '收到',
                        confirmed: '确认',
                        in_progress: '处置',
                        feedback: '反馈',
                        completed: '完成',
                      };
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
                  {stepIdx < TASK_STEPS.length - 1 && (
                    <div style={{ marginTop: 'var(--spacing-sm)' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => handleAdvanceStatus(task.id, task.status)}
                      >
                        推进到: {TASK_STEPS[stepIdx + 1] === 'confirmed' ? '确认' :
                          TASK_STEPS[stepIdx + 1] === 'in_progress' ? '处置' :
                          TASK_STEPS[stepIdx + 1] === 'feedback' ? '反馈' : '完成'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </>
      )}

      {activeTab === 'notifications' && (
        <>
          {(notifications || []).length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">📢</div><div className="empty-state-text">暂无通知</div></div>
          ) : (
            (notifications || []).map(notif => (
              <div key={notif.id} className="notification-card">
                <div className="notification-card-header">
                  <span className="notification-card-title">{notif.title}</span>
                  <StatusBadge status={notif.status} statusMap={NOTIFICATION_STATUS_MAP} />
                </div>
                <div className="notification-card-body">{notif.content}</div>
                <div className="notification-card-footer">
                  <span>渠道: {notif.channel === 'push' ? '推送' : notif.channel === 'sms' ? '短信' : notif.channel === 'wechat' ? '微信' : '广播'}</span>
                  <span>送达: {notif.deliveredCount} / 失败: {notif.failedCount}</span>
                  <span>创建于 {dayjs(notif.createdAt).fromNow()}</span>
                  {notif.status === 'pending' && (
                    <button className="btn btn-primary btn-sm" onClick={() => setConfirmDispatch(notif.id)}>
                      发送
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </>
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
                value={newTask.type}
                onChange={e => setNewTask(prev => ({ ...prev, type: e.target.value as TaskType }))}
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
                value={newTask.title || ''}
                onChange={e => setNewTask(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">描述</label>
              <textarea
                className="form-textarea"
                placeholder="任务详细描述"
                value={newTask.description || ''}
                onChange={e => setNewTask(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">优先级</label>
                <select
                  className="form-select"
                  value={newTask.priority}
                  onChange={e => setNewTask(prev => ({ ...prev, priority: e.target.value as TaskPriority }))}
                >
                  <option value="low">低</option>
                  <option value="medium">中</option>
                  <option value="high">高</option>
                  <option value="urgent">紧急</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">区域</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="目标区域"
                  value={newTask.areaName || ''}
                  onChange={e => setNewTask(prev => ({ ...prev, areaName: e.target.value }))}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">截止时间</label>
              <input
                type="datetime-local"
                className="form-input"
                value={newTask.deadline || ''}
                onChange={e => setNewTask(prev => ({ ...prev, deadline: e.target.value }))}
              />
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

      {/* 发送通知确认 */}
      <ConfirmDialog
        open={!!confirmDispatch}
        title="确认发送通知"
        message="确定要发送此通知吗？发送后将无法撤回。"
        confirmText="确认发送"
        variant="warning"
        onConfirm={handleDispatch}
        onCancel={() => setConfirmDispatch(null)}
      />
    </div>
  );
}
