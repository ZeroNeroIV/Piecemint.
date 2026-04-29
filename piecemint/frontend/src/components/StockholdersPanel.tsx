import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { Plus, X } from 'lucide-react';
import { useFinanceData } from '../context/FinanceDataContext';
import EntityCategorySelect from './EntityCategorySelect';
import { API_BASE } from '../lib/apiBase';

/**
 * Stockholder list (names, category, share %). Shown on the Stockholders plugin page.
 */
export default function StockholdersPanel() {
  const { stockholders, refresh } = useFinanceData();
  const panelRef = useRef<HTMLElement | null>(null);
  const [removedIds, setRemovedIds] = useState<string[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: '',
    email: '',
    share_percent: '',
    notes: '',
  });
  const [error, setError] = useState<string | null>(null);
  const visibleRows = useMemo(
    () => stockholders.filter((s: { id: string }) => !removedIds.includes(s.id)),
    [stockholders, removedIds]
  );

  useEffect(() => {
    const closeOpenMenus = () => {
      const panel = panelRef.current;
      if (!panel) return;
      const openMenus = panel.querySelectorAll('details[open]');
      openMenus.forEach((menu) => {
        menu.removeAttribute('open');
      });
    };

    const handlePointerDown = (event: PointerEvent) => {
      const panel = panelRef.current;
      if (!panel) return;
      const target = event.target as Node | null;
      if (!target) return;
      const openMenus = Array.from(panel.querySelectorAll('details[open]'));
      if (openMenus.length === 0) return;
      const clickedInsideOpenMenu = openMenus.some((menu) => menu.contains(target));
      if (!clickedInsideOpenMenu) closeOpenMenus();
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeOpenMenus();
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const resetForm = () => {
    setEditingId(null);
    setForm({ name: '', email: '', share_percent: '', notes: '' });
  };

  const startEdit = (s: { id: string; name: string; email: string; share_percent: number | null; notes?: string }) => {
    setEditingId(s.id);
    setForm({
      name: s.name,
      email: s.email || '',
      share_percent: s.share_percent != null ? String(s.share_percent) : '',
      notes: s.notes || '',
    });
    setError(null);
  };

  const submit = async () => {
    if (!form.name.trim()) {
      setError('Name is required.');
      return;
    }
    const shareRaw = form.share_percent.trim();
    const parsedShare = Number(shareRaw);
    if (shareRaw !== '' && (!Number.isFinite(parsedShare) || parsedShare < 0 || parsedShare > 100)) {
      setError('Share % must be between 0 and 100.');
      return;
    }
    const share = shareRaw === '' ? null : parsedShare;
    setError(null);
    const body = {
      name: form.name.trim(),
      email: form.email.trim(),
      share_percent: share,
      notes: form.notes.trim(),
    };
    try {
      if (editingId) {
        await axios.put(`${API_BASE}/core/stockholders/${encodeURIComponent(editingId)}`, body);
      } else {
        await axios.post(`${API_BASE}/core/stockholders`, body);
      }
      resetForm();
      await refresh();
    } catch (e: unknown) {
      if (axios.isAxiosError(e)) {
        const detail = (e.response?.data as { detail?: unknown } | undefined)?.detail;
        setError(typeof detail === 'string' ? detail : 'Could not save stockholder.');
      } else {
        setError('Could not save stockholder.');
      }
    }
  };

  const removeFromView = (id: string) => {
    setRemovedIds((prev) => (prev.includes(id) ? prev : [...prev, id]));
  };

  const deleteRow = async (id: string, name: string) => {
    if (!window.confirm(`Delete stockholder "${name}"? This cannot be undone.`)) return;
    setError(null);
    try {
      await axios.delete(`${API_BASE}/core/stockholders/${encodeURIComponent(id)}`);
      if (editingId === id) resetForm();
      setRemovedIds((prev) => prev.filter((x) => x !== id));
      await refresh();
    } catch (e: unknown) {
      if (axios.isAxiosError(e)) {
        const detail = (e.response?.data as { detail?: unknown } | undefined)?.detail;
        setError(typeof detail === 'string' ? detail : 'Could not delete stockholder.');
      } else {
        setError('Could not delete stockholder.');
      }
    }
  };

  return (
    <section ref={panelRef}>
      <div className="mb-5 card p-4 md:p-5">
        <div className="flex items-center justify-between gap-3 mb-3">
          <h3 className="text-sm font-bold tracking-widest uppercase text-ink-black/60">
            {editingId ? 'Edit stockholder' : 'Add stockholder'}
          </h3>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="inline-flex items-center gap-1 rounded-full border border-ink-black/20 px-3 py-1.5 text-xs font-medium hover:bg-ink-black hover:text-canvas-cream transition-colors"
              aria-label="Cancel edit"
            >
              <X size={14} />
              Cancel
            </button>
          )}
        </div>
        {error && (
          <p className="mb-3 rounded-xl border border-signal-orange/40 bg-signal-orange/10 px-3 py-2 text-sm text-ink-black">
            {error}
          </p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="Name"
            className="w-full border border-ink-black/20 rounded-xl px-3 py-2 text-sm"
            aria-label="Stockholder name"
          />
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
            placeholder="Email"
            className="w-full border border-ink-black/20 rounded-xl px-3 py-2 text-sm"
            aria-label="Stockholder email"
          />
          <input
            type="number"
            min={0}
            max={100}
            step="0.1"
            value={form.share_percent}
            onChange={(e) => setForm((p) => ({ ...p, share_percent: e.target.value }))}
            placeholder="Share %"
            className="w-full border border-ink-black/20 rounded-xl px-3 py-2 text-sm"
            aria-label="Stockholder share percent"
          />
          <button
            type="button"
            onClick={() => void submit()}
            className="inline-flex items-center justify-center gap-1 rounded-full border border-ink-black/20 px-3 py-2 text-sm font-medium hover:bg-ink-black hover:text-canvas-cream transition-colors"
            aria-label={editingId ? 'Save stockholder changes' : 'Add stockholder'}
          >
            <Plus size={15} />
            {editingId ? 'Save' : 'Add'}
          </button>
        </div>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-left min-w-[480px]">
          <thead>
            <tr className="border-b border-ink-black/10">
              <th className="pb-4 font-medium">Name</th>
              <th className="pb-4 font-medium">Category</th>
              <th className="pb-4 font-medium">Email</th>
              <th className="pb-4 font-medium">Share %</th>
              <th className="pb-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {visibleRows.map(
              (s: { id: string; name: string; email: string; share_percent: number | null; notes?: string }) => (
                <tr key={s.id} className="border-b border-ink-black/5 last:border-0">
                  <td className="py-4 font-medium">{s.name}</td>
                  <td className="py-4 align-top">
                    <EntityCategorySelect kind="stockholder" entityId={s.id} />
                  </td>
                  <td className="py-4 text-sm text-ink-black/70">{s.email || '—'}</td>
                  <td className="py-4 tabular-nums">
                    {s.share_percent != null ? `${Number(s.share_percent).toFixed(1)}%` : '—'}
                  </td>
                  <td className="py-4 text-right">
                    <details className="relative inline-block text-left">
                      <summary
                        className="inline-flex cursor-pointer list-none items-center rounded-full border border-ink-black/20 px-3 py-1.5 text-xs font-medium text-ink-black transition-colors hover:bg-ink-black hover:text-canvas-cream"
                        aria-label={`Open actions for ${s.name}`}
                      >
                        Actions
                      </summary>
                      <div className="absolute right-0 z-10 mt-1 min-w-[140px] rounded-2xl border border-ink-black/15 bg-white p-1.5 shadow-[0px_8px_24px_rgba(0,0,0,0.08)]">
                        <button
                          type="button"
                          onClick={(e) => {
                            startEdit(s);
                            const details = (e.currentTarget.closest('details') as HTMLDetailsElement | null);
                            details?.removeAttribute('open');
                          }}
                          className="w-full rounded-xl px-3 py-2 text-left text-xs font-medium text-ink-black hover:bg-ink-black/5"
                          aria-label={`Edit ${s.name}`}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            removeFromView(s.id);
                            const details = (e.currentTarget.closest('details') as HTMLDetailsElement | null);
                            details?.removeAttribute('open');
                          }}
                          className="w-full rounded-xl px-3 py-2 text-left text-xs font-medium text-ink-black hover:bg-ink-black/5"
                          aria-label={`Remove ${s.name} from current view`}
                        >
                          Remove
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            void deleteRow(s.id, s.name);
                            const details = (e.currentTarget.closest('details') as HTMLDetailsElement | null);
                            details?.removeAttribute('open');
                          }}
                          className="w-full rounded-xl px-3 py-2 text-left text-xs font-medium text-signal-orange hover:bg-signal-orange/10"
                          aria-label={`Delete ${s.name}`}
                        >
                          Delete
                        </button>
                      </div>
                    </details>
                  </td>
                </tr>
              )
            )}
            {visibleRows.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-ink-black/60">
                  No stockholders in the current view.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
