'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { fetchSettings, updateSettings } from '@/lib/api';
import { getRoleLabel } from '@/lib/auth';
import ConfirmDialog from '@/components/ConfirmDialog';
import type {
  SettingsConfig, RiskRuleWeight, NotificationStrategy,
  NotificationChannel, RiskLevel, DataSourceConfig,
} from '@/lib/types';

const CHANNEL_LABELS: Record<NotificationChannel, string> = {
  push: '📱 推送',
  sms: '💬 短信',
  wechat: '🟢 微信',
  broadcast: '📻 广播',
};

const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  normal: '正常',
  attention: '关注',
  high: '高危',
  critical: '极高',
};

const TRUST_LEVEL_LABELS: Record<string, string> = {
  high: '高可信',
  medium: '中等',
  low: '低可信',
};

const TRUST_LEVEL_COLORS: Record<string, string> = {
  high: 'var(--color-safe)',
  medium: 'var(--color-warning)',
  low: 'var(--color-danger)',
};

export default function SettingsPage() {
  const { data: settings, error, isLoading, mutate } = useSWR<SettingsConfig>(
    'settings',
    fetchSettings
  );

  const [localSettings, setLocalSettings] = useState<SettingsConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmSave, setConfirmSave] = useState(false);

  const currentSettings = localSettings || settings;

  const handleWeightChange = (factor: string, weight: number) => {
    if (!currentSettings) return;
    setLocalSettings({
      ...currentSettings,
      riskRuleWeights: currentSettings.riskRuleWeights.map(w =>
        w.factor === factor ? { ...w, weight } : w
      ),
    });
  };

  const handleWeightToggle = (factor: string) => {
    if (!currentSettings) return;
    setLocalSettings({
      ...currentSettings,
      riskRuleWeights: currentSettings.riskRuleWeights.map(w =>
        w.factor === factor ? { ...w, enabled: !w.enabled } : w
      ),
    });
  };

  const handleNotifChange = (channel: NotificationChannel, field: string, value: boolean | RiskLevel | number) => {
    if (!currentSettings) return;
    setLocalSettings({
      ...currentSettings,
      notificationStrategies: currentSettings.notificationStrategies.map(s =>
        s.channel === channel ? { ...s, [field]: value } : s
      ),
    });
  };

  const handleDataSourceToggle = (index: number) => {
    if (!currentSettings) return;
    const newSources = [...currentSettings.dataSources];
    newSources[index] = { ...newSources[index], enabled: !newSources[index].enabled };
    setLocalSettings({ ...currentSettings, dataSources: newSources });
  };

  const handleDataSourceRefreshChange = (index: number, minutes: number) => {
    if (!currentSettings) return;
    const newSources = [...currentSettings.dataSources];
    newSources[index] = { ...newSources[index], refreshIntervalMinutes: minutes };
    setLocalSettings({ ...currentSettings, dataSources: newSources });
  };

  const handleDataSourceTrustChange = (index: number, level: 'high' | 'medium' | 'low') => {
    if (!currentSettings) return;
    const newSources = [...currentSettings.dataSources];
    newSources[index] = { ...newSources[index], trustLevel: level };
    setLocalSettings({ ...currentSettings, dataSources: newSources });
  };

  const handleSave = async () => {
    if (!currentSettings) return;
    setSaving(true);
    await updateSettings(currentSettings);
    setSaving(false);
    setConfirmSave(false);
    setLocalSettings(null);
    mutate();
  };

  const totalWeight = currentSettings?.riskRuleWeights
    .filter(w => w.enabled)
    .reduce((sum, w) => sum + w.weight, 0) || 0;
  const weightValid = Math.abs(totalWeight - 1) < 0.01;

  if (isLoading) {
    return <div className="empty-state"><div className="empty-state-icon">⏳</div><div className="empty-state-text">加载中...</div></div>;
  }

  if (error || !currentSettings) {
    return <div className="empty-state"><div className="empty-state-icon">❌</div><div className="empty-state-text">加载失败</div></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-lg">
        <h2 className="section-title" style={{ marginBottom: 0 }}>设置</h2>
        {localSettings && (
          <div className="flex gap-sm">
            <button className="btn btn-secondary" onClick={() => setLocalSettings(null)}>重置</button>
            <button className="btn btn-primary" onClick={() => setConfirmSave(true)}>保存设置</button>
          </div>
        )}
      </div>

      {/* 数据源配置 */}
      <div className="settings-section">
        <h3 className="settings-section-title">📡 数据源配置</h3>
        {currentSettings.dataSources.map((source, i) => (
          <div key={source.name} style={{
            padding: 'var(--spacing-md) 0',
            borderBottom: '1px solid var(--color-border-light)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div>
                <div className="settings-row-label">{source.name}</div>
                <div className="settings-row-desc" style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>
                  {source.url}
                </div>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={source.enabled}
                  onChange={() => handleDataSourceToggle(i)}
                  style={{ width: 16, height: 16, accentColor: 'var(--color-primary)' }}
                />
                <span style={{ fontSize: 'var(--font-size-sm)' }}>{source.enabled ? '启用' : '禁用'}</span>
              </label>
            </div>
            {source.enabled && (
              <div style={{ display: 'flex', gap: 'var(--spacing-lg)', alignItems: 'center' }}>
                <div>
                  <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>刷新间隔: </span>
                  <select
                    className="form-select"
                    style={{ width: 80, padding: '2px 4px', fontSize: 'var(--font-size-xs)' }}
                    value={source.refreshIntervalMinutes || 5}
                    onChange={e => handleDataSourceRefreshChange(i, Number(e.target.value))}
                  >
                    <option value={1}>1 分钟</option>
                    <option value={3}>3 分钟</option>
                    <option value={5}>5 分钟</option>
                    <option value={10}>10 分钟</option>
                    <option value={15}>15 分钟</option>
                    <option value={30}>30 分钟</option>
                  </select>
                </div>
                <div>
                  <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>信任等级: </span>
                  <select
                    className="form-select"
                    style={{ width: 80, padding: '2px 4px', fontSize: 'var(--font-size-xs)' }}
                    value={source.trustLevel || 'medium'}
                    onChange={e => handleDataSourceTrustChange(i, e.target.value as 'high' | 'medium' | 'low')}
                  >
                    <option value="high">高</option>
                    <option value="medium">中</option>
                    <option value="low">低</option>
                  </select>
                  <span style={{
                    display: 'inline-block',
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: TRUST_LEVEL_COLORS[source.trustLevel || 'medium'],
                    marginLeft: 4,
                  }} />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 风险规则权重 */}
      <div className="settings-section">
        <h3 className="settings-section-title">
          ⚖️ 风险规则权重
          {!weightValid && (
            <span style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', fontWeight: 'normal', marginLeft: 8 }}>
              权重总和需为 100%（当前: {Math.round(totalWeight * 100)}%）
            </span>
          )}
        </h3>
        {currentSettings.riskRuleWeights.map(rule => (
          <div key={rule.factor} className="settings-row">
            <div>
              <div className="settings-row-label">{rule.label}</div>
              <div className="settings-row-desc">因子: {rule.factor}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                type="range"
                className="weight-slider"
                min={0}
                max={100}
                value={Math.round(rule.weight * 100)}
                disabled={!rule.enabled}
                onChange={e => handleWeightChange(rule.factor, Number(e.target.value) / 100)}
              />
              <span className="weight-value">{Math.round(rule.weight * 100)}%</span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={rule.enabled}
                  onChange={() => handleWeightToggle(rule.factor)}
                  style={{ width: 16, height: 16, accentColor: 'var(--color-primary)' }}
                />
              </label>
            </div>
          </div>
        ))}
      </div>

      {/* 通知策略 */}
      <div className="settings-section">
        <h3 className="settings-section-title">📢 通知策略</h3>
        {currentSettings.notificationStrategies.map(strategy => (
          <div key={strategy.channel} style={{
            padding: 'var(--spacing-md) 0',
            borderBottom: '1px solid var(--color-border-light)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <div>
                <div className="settings-row-label">{CHANNEL_LABELS[strategy.channel]}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontSize: 'var(--font-size-sm)' }}>
                  <input
                    type="checkbox"
                    checked={strategy.enabled}
                    onChange={e => handleNotifChange(strategy.channel, 'enabled', e.target.checked)}
                    style={{ width: 16, height: 16, accentColor: 'var(--color-primary)' }}
                  />
                  启用
                </label>
              </div>
            </div>
            {strategy.enabled && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 'var(--spacing-sm)', fontSize: 'var(--font-size-sm)' }}>
                <div>
                  <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>风险阈值: </span>
                  <select
                    className="form-select"
                    style={{ width: 80, padding: '2px 4px', fontSize: 'var(--font-size-xs)' }}
                    value={strategy.riskLevelThreshold}
                    onChange={e => handleNotifChange(strategy.channel, 'riskLevelThreshold', e.target.value as RiskLevel)}
                  >
                    <option value="normal">正常</option>
                    <option value="attention">关注</option>
                    <option value="high">高危</option>
                    <option value="critical">极高</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={strategy.autoDispatch}
                      onChange={e => handleNotifChange(strategy.channel, 'autoDispatch', e.target.checked)}
                      style={{ width: 16, height: 16, accentColor: 'var(--color-primary)' }}
                    />
                    自动派发
                  </label>
                </div>
                <div>
                  <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>重试次数: </span>
                  <select
                    className="form-select"
                    style={{ width: 60, padding: '2px 4px', fontSize: 'var(--font-size-xs)' }}
                    value={strategy.retryCount ?? 3}
                    onChange={e => handleNotifChange(strategy.channel, 'retryCount', Number(e.target.value))}
                  >
                    <option value={0}>0</option>
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={5}>5</option>
                  </select>
                </div>
                <div>
                  <span className="text-hint" style={{ fontSize: 'var(--font-size-xs)' }}>升级超时: </span>
                  <select
                    className="form-select"
                    style={{ width: 80, padding: '2px 4px', fontSize: 'var(--font-size-xs)' }}
                    value={strategy.escalationTimeoutMinutes ?? 10}
                    onChange={e => handleNotifChange(strategy.channel, 'escalationTimeoutMinutes', Number(e.target.value))}
                  >
                    <option value={5}>5 分钟</option>
                    <option value={10}>10 分钟</option>
                    <option value={15}>15 分钟</option>
                    <option value={30}>30 分钟</option>
                    <option value={60}>60 分钟</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 角色权限 */}
      <div className="settings-section">
        <h3 className="settings-section-title">👥 角色权限概览</h3>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table" style={{ fontSize: 'var(--font-size-sm)' }}>
            <thead>
              <tr>
                <th>角色</th>
                <th>报告</th>
                <th>避险场所</th>
                <th>任务</th>
                <th>通知</th>
                <th>审计</th>
                <th>设置</th>
                <th>精确位置</th>
              </tr>
            </thead>
            <tbody>
              {[
                {
                  role: 'admin', label: '管理员', icon: '👑',
                  report: '核验/驳回', shelter: '查看/编辑', task: '创建/更新',
                  notification: '创建/派发', audit: '查看', settings: '查看/编辑', location: '✓',
                },
                {
                  role: 'community', label: '社区', icon: '🏘️',
                  report: '核验/驳回', shelter: '仅查看', task: '仅更新',
                  notification: '仅查看', audit: '查看', settings: '—', location: '—',
                },
                {
                  role: 'emergency_station', label: '应急站', icon: '🚒',
                  report: '核验/驳回', shelter: '查看/编辑', task: '创建/更新',
                  notification: '创建', audit: '查看', settings: '—', location: '✓',
                },
              ].map(r => (
                <tr key={r.role}>
                  <td>
                    <div className="flex items-center gap-sm">
                      <span>{r.icon}</span>
                      <span className="font-bold">{r.label}</span>
                      <span className={`role-badge role-${r.role}`}>{r.role}</span>
                    </div>
                  </td>
                  <td>{r.report}</td>
                  <td>{r.shelter}</td>
                  <td>{r.task}</td>
                  <td>{r.notification}</td>
                  <td>{r.audit}</td>
                  <td>{r.settings}</td>
                  <td style={{ textAlign: 'center' }}>{r.location}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 保存确认 */}
      <ConfirmDialog
        open={confirmSave}
        title="确认保存设置"
        message="确定要保存当前设置吗？修改将立即生效。"
        confirmText="确认保存"
        variant="warning"
        onConfirm={handleSave}
        onCancel={() => setConfirmSave(false)}
      />
    </div>
  );
}
