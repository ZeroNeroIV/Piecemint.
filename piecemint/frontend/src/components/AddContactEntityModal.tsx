import { useCallback, useEffect, useId, useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { API_BASE } from '../lib/apiBase';

type Kind = 'client' | 'supplier';

type AddContactEntityModalProps = {
  kind: Kind;
  onClose: () => void;
  onCreated: () => void;
};

function overlayMountEl(): HTMLElement {
  return document.getElementById('ff-overlay-root') ?? document.body;
}

export default function AddContactEntityModal({ kind, onClose, onCreated }: AddContactEntityModalProps) {
  const titleId = useId();
  const label = kind === 'client' ? 'client' : 'supplier';
  const title = kind === 'client' ? 'Add client' : 'Add supplier';

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [totalBilled, setTotalBilled] = useState('0');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  const submit = useCallback(async () => {
    if (!name.trim()) {
      setError('Name is required.');
      return;
    }
    const tb = parseFloat(totalBilled);
    if (!Number.isFinite(tb) || tb < 0) {
      setError('Total billed must be a non-negative number.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const path = kind === 'client' ? 'clients' : 'suppliers';
      await axios.post(`${API_BASE}/core/${path}`, {
        name: name.trim(),
        email: email.trim(),
        total_billed: tb,
      });
      onCreated();
      onClose();
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.data && typeof e.response.data === 'object') {
        const d = e.response.data as { detail?: unknown };
        if (typeof d.detail === 'string') {
          setError(d.detail);
        } else {
          setError(e.message);
        }
      } else if (e instanceof Error) {
        setError(e.message);
      } else {
        setError('Could not save. Is the API running?');
      }
    } finally {
      setBusy(false);
    }
  }, [kind, name, email, totalBilled, onClose, onCreated]);

  const shell = (
    <div className="fixed inset-0 z-[1] flex items-end justify-center p-0 sm:items-center sm:p-4" role="presentation">
      <button
        type="button"
        className="absolute inset-0 h-full w-full cursor-default border-0 bg-ink-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative w-full max-h-[90dvh] overflow-y-auto border border-ink-black/10 bg-canvas-cream p-6 shadow-2xl outline-none sm:max-w-md sm:rounded-3xl sm:p-8"
      >
        <div className="mb-6 flex items-start justify-between gap-3">
          <div>
            <p className="mb-1 text-xs font-bold uppercase tracking-widest text-ink-black/50">New {label}</p>
            <h2 id={titleId} className="pr-2 text-xl font-medium text-ink-black">
              {title}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="h-10 w-10 shrink-0 rounded-full border border-ink-black/20 text-lg leading-none hover:bg-ink-black/5"
            aria-label="Close dialog"
          >
            ×
          </button>
        </div>

        <div className="space-y-4 text-sm">
          <label className="block">
            <span className="text-xs font-medium text-ink-black/60">Name</span>
            <input
              className="mt-1 w-full rounded-xl border border-ink-black/20 px-3 py-2"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Company or person"
              autoComplete="organization"
              autoFocus
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-black/60">Email</span>
            <input
              type="email"
              className="mt-1 w-full rounded-xl border border-ink-black/20 px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="optional@email.com"
              autoComplete="email"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-black/60">Total billed ($)</span>
            <input
              type="number"
              min={0}
              step="0.01"
              className="mt-1 w-full rounded-xl border border-ink-black/20 px-3 py-2 tabular-nums"
              value={totalBilled}
              onChange={(e) => setTotalBilled(e.target.value)}
            />
          </label>
          {error && <p className="text-sm text-signal-orange">{error}</p>}
        </div>

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" onClick={onClose} className="pill-button-secondary w-full sm:w-auto" disabled={busy}>
            Cancel
          </button>
          <button
            type="button"
            onClick={() => void submit()}
            className="pill-button w-full sm:w-auto disabled:opacity-50"
            disabled={busy}
          >
            {busy ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );

  if (typeof document === 'undefined') return null;
  return createPortal(shell, overlayMountEl());
}
