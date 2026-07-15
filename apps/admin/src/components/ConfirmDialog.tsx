'use client';

import { useEffect } from 'react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'default';
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  variant = 'default',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  if (!open) return null;

  const variantClass = variant === 'danger' ? 'dialog-danger'
    : variant === 'warning' ? 'dialog-warning' : 'dialog-default';

  return (
    <div className="dialog-overlay" onClick={onCancel}>
      <div className={`dialog-box ${variantClass}`} onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <span className="dialog-icon">
            {variant === 'danger' ? '⚠️' : variant === 'warning' ? '⚡' : '❓'}
          </span>
          <h3 className="dialog-title">{title}</h3>
        </div>
        <p className="dialog-message">{message}</p>
        <div className="dialog-actions">
          <button className="btn btn-secondary" onClick={onCancel}>
            {cancelText}
          </button>
          <button
            className={`btn ${variant === 'danger' ? 'btn-danger' : 'btn-primary'}`}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
