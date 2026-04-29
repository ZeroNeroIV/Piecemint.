import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { API_BASE } from '../lib/apiBase';

type AddTransactionModalProps = {
  onClose: () => void;
  onCreated: () => void;
};

function overlayMountEl(): HTMLElement {
  return document.getElementById('ff-overlay-root') ?? document.body;
}

function todayIso(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export default function AddTransactionModal({ onClose, onCreated }: AddTransactionModalProps) {
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const dateInputRef = useRef<HTMLInputElement>(null);

  const [date, setDate] = useState(todayIso());
  const [amountRaw, setAmountRaw] = useState('');
  const [txType, setTxType] = useState<'income' | 'expense'>('expense');
  const [category, setCategory] = useState('');
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  useEffect(() => {
    const root = panelRef.current;
    if (!root) return;
    const sel =
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const focusables = () =>
      Array.from(root.querySelectorAll<HTMLElement>(sel)).filter(
        (el) => !el.hasAttribute('disabled')
      );
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      const list = focusables();
      if (list.length === 0) return;
      const active = document.activeElement as HTMLElement | null;
      if (!active || !root.contains(active)) return;
      const first = list[0];
      const last = list[list.length - 1];
      if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      } else if (e.shiftKey && active === first) {
        e.preventDefault();
        last.focus();
      }
    };
    root.addEventListener('keydown', onKeyDown);
    queueMicrotask(() => dateInputRef.current?.focus());
    return () => root.removeEventListener('keydown', onKeyDown);
  }, []);

  const submit = useCallback(async () => {
    const cat = category.trim();
    if (!cat) {
      setError('Category is required.');
      return;
    }
    const n = parseFloat(amountRaw.replace(/,/g, ''));
    if (!Number.isFinite(n) || n <= 0) {
      setError('Amount must be a positive number.');
      return;
    }
    const iso = /^\d{4}-\d{2}-\d{2}$/.test(date);
    if (!iso) {
      setError('Date must be YYYY-MM-DD.');
      return;
    }
    const signed = txType === 'income' ? n : -n;
    setBusy(true);
    setError(null);
    try {
      await axios.post(`${API_BASE}/core/transactions`, {
        amount: signed,
        date,
        type: txType,
        category: cat,
        notes: notes.trim(),
        is_recurring: false,
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
  }, [amountRaw, category, date, notes, onClose, onCreated, txType]);

  const shell = (
    <div className="fixed inset-0 z-[1] flex items-end justify-center p-0 sm:items-center sm:p-4" role="presentation">
      <button
        type="button"
        tabIndex={-1}
        className="absolute inset-0 h-full w-full cursor-default border-0 bg-ink-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative w-full max-h-[90dvh] overflow-y-auto border border-ink-black/10 bg-canvas-cream p-6 shadow-2xl outline-none sm:max-w-md sm:rounded-3xl sm:p-8"
      >
        <div className="mb-6 flex items-start justify-between gap-3">
          <div>
            <p className="mb-1 text-xs font-bold uppercase tracking-widest text-ink-black/50">New entry</p>
            <h2 id={titleId} className="pr-2 text-xl font-medium text-ink-black">
              Add transaction
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
            <span className="text-xs font-medium text-ink-black/60">Date</span>
            <input
              ref={dateInputRef}
              type="date"
              className="mt-1 w-full rounded-xl border border-ink-black/20 px-3 py-2 tabular-nums"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-black/60">Amount ($)</span>
            <input
              type="number"
              min={0}
              step="0.01"
              className="mt-1 w-full rounded-xl border border-ink-black/20 px-3 py-2 tabular-nums"
              value={amountRaw}
              onChange={(e) => setAmountRaw(e.target.value)}
              placeholder="0.00"
            />
            <span className="mt-1 block text-xs text-ink-black/50">Enter a positive amount; type below sets sign.</span>
          </label>
          <fieldset className="border-0 p-0 m-0">
            <legend className="text-xs font-medium text-ink-black/60 mb-2">Type</legend>
            <div className="flex gap-4">
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="tx-type"
                  checked={txType === 'income'}
                  onChange={() => setTxType('income')}
                />
                Income
              </label>
              <label className="inline-flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="tx-type"
                  checked={txType === 'expense'}
                  onChange={() => setTxType('expense')}
                />
                Expense
              </label>
            </div>
          </fieldset>
          <label className="block">
            <span className="text-xs font-medium text-ink-black/60">Category</span>
            <input
              className="mt-1 w-full rounded-xl border border-ink-black/20 px-3 py-2"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. Consulting, AWS Cloud"
            />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-ink-black/60">Memo / description</span>
            <textarea
              className="mt-1 w-full min-h-[88px] rounded-xl border border-ink-black/20 px-3 py-2 resize-y"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional details"
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
