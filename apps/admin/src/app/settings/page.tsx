'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { fetchSettings, updateSettings } from '@/lib/api';
import ConfirmDialog from '@/components/ConfirmDialog';
import type { SettingsConfig, RiskRuleWeight, NotificationStrategy, NotificationChannel, RiskLevel } from '@/lib/types';

const CHANNEL_LABELS: Record<NotificationChannel, string> = {
  push: '推送',
  sms: '短信',
  wechat: '微信',
  broadcast: '广播',
};

const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  normal: '正常',
  attention: '关注',
  high: '高危',
  critical: '极高',
};

export default function SettingsPage() {
  const { data: settings, error, isLoading, mutate } = useSWR<SettingsConfig>(
    'settings',
    fetchSettings
  );

  const [localSettings, setLocalSettings] = useState<SettingsConfig | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmSave, setConfirmSave] = useState(false);

  // 初始化本地设置
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

  const handleNotifChange = (channel: NotificationChannel, field: string, value: boolean | RiskLevel) => {
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
          <div key={source.name} className="settings-row">
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
          <div key={strategy.channel} className="settings-row">
            <div>
              <div className="settings-row-label">{CHANNEL_LABELS[strategy.channel]}</div>
              <div className="settings-row-desc">
                自动派发: {strategy.autoDispatch ? '是' : '否'} ·
                阈值: {RISK_LEVEL_LABELS[strategy.riskLevelThreshold]}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <select
                className="form-select"
                style={{ width: 100, padding: '4px 8px' }}
                value={strategy.riskLevelThreshold}
                onChange={e => handleNotifChange(strategy.channel, 'riskLevelThreshold', e.target.value as RiskLevel)}
              >
                <option value="normal">正常</option>
                <option value="attention">关注</option>
                <option value="high">高危</option>
                <option value="critical">极高</option>
              </select>
              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontSize: 'var(--font-size-sm)' }}>
                <input
                  type="checkbox"
                  checked={strategy.autoDispatch}
                  onChange={e => handleNotifChange(strategy.channel, 'autoDispatch', e.target.checked)}
                  style={{ width: 16, height: 16, accentColor: 'var(--color-primary)' }}
                />
                自动
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={strategy.enabled}
                  onChange={e => handleNotifChange(strategy.channel, 'enabled', e.target.checked)}
                  style={{ width: 16, height: 16, accentColor: 'var(--color-primary)' }}
                />
              </label>
            </div>
          </div>
        ))}
      </div>

      {/* 角色管理（只读展示） */}
      <div className="settings-section">
        <h3 className="settings-section-title">👥 角色权限</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--spacing-md)' }}>
          {[
            { role: 'admin', label: '管理员', desc: '全部权限：报告核验、任务管理、通知派发、设置修改、审计查看', icon: '👑' },
            { role: 'community', label: '社区', desc: '报告核验、任务查看与更新、通知查看、审计查看', icon: '🏘️' },
            { role: 'emergency_station', label: '应急站', desc: '报告核验、避险场所管理、任务创建与更新、通知创建', icon: '🚒' },
          ].map(r => (
            <div key={r.role} style={{
              border: '1px solid var(--color-border-light)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-md)',
            }}>
              <div className="flex items-center gap-sm mb-sm">
                <span style={{ fontSize: 24 }}>{r.icon}</span>
                <span className="font-bold">{r.label}</span>
                <span className={`role-badge role-${r.role}`}>{r.role}</span>
              </div>
              <div className="text-secondary" style={{ fontSize: 'var(--font-size-sm)' }}>{r.desc}</div>
            </div>
          ))}
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
