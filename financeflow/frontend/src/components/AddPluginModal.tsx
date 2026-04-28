import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { API_BASE } from '../lib/apiBase';

type AddPluginModalProps = {
  onClose: () => void;
  onInstalled: () => void;
};

const ID_RE = /^[a-z][a-z0-9_]*$/;

type InstallMode = 'paste' | 'zip';

function overlayMountEl(): HTMLElement {
  return document.getElementById('ff-overlay-root') ?? document.body;
}

export default function AddPluginModal({ onClose, onInstalled }: AddPluginModalProps) {
  const titleId = useId();
  const fileRef = useRef<HTMLInputElement>(null);
  const zipRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<InstallMode>('zip');
  const [pluginId, setPluginId] = useState('');
  const [logicPy, setLogicPy] = useState('');
  const [manifestYaml, setManifestYaml] = useState('');
  const [useCustomManifest, setUseCustomManifest] = useState(false);
  const [overwrite, setOverwrite] = useState(false);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  const onPickFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      setLogicPy(String(r.result || ''));
      setError(null);
    };
    r.readAsText(f, 'utf-8');
  }, []);

  const onPickZip = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setZipFile(f ?? null);
    setError(null);
  }, []);

  const submitZip = async () => {
    if (!zipFile) {
      setError('Choose a .zip from the marketplace (one top-level folder, e.g. my_plugin/logic.py).');
      return;
    }
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const fd = new FormData();
      fd.append('file', zipFile);
      fd.append('overwrite', overwrite ? 'true' : 'false');
      const { data } = await axios.post<{
        ok: boolean;
        plugin_id?: string;
        message?: string;
        path?: string;
      }>(`${API_BASE}/dev/plugins/install_zip`, fd);
      if (data?.ok) {
        setSuccess(
          data.message ||
            `Plugin “${data.plugin_id ?? '…'}” extracted. Restart the API, then refresh the plugin list.`
        );
        onInstalled();
      } else {
        setError('Unexpected response from server.');
      }
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.data) {
        const d = e.response.data as { detail?: string | { msg: string }[] };
        if (typeof d.detail === 'string') {
          setError(d.detail);
        } else if (Array.isArray(d.detail) && d.detail[0] && 'msg' in d.detail[0]) {
          setError(String((d.detail[0] as { msg: string }).msg));
        } else {
          setError(e.message);
        }
      } else {
        setError('Upload failed. Is the API running and FF_DISABLE_PLUGIN_UPLOAD off?');
      }
    } finally {
      setBusy(false);
    }
  };

  const submitPaste = async () => {
    setError(null);
    setSuccess(null);
    const id = pluginId.trim();
    if (!id || !ID_RE.test(id)) {
      setError('Plugin id must start with a letter and use only lowercase letters, numbers, and underscores.');
      return;
    }
    if (logicPy.trim().length < 20) {
      setError('Paste or choose a logic.py that defines a FastAPI router (e.g. router = APIRouter()).');
      return;
    }
    setBusy(true);
    try {
      const { data } = await axios.post<{
        ok: boolean;
        message?: string;
        path?: string;
      }>(`${API_BASE}/dev/plugins/install`, {
        plugin_id: id,
        logic_py: logicPy,
        manifest_yaml: useCustomManifest && manifestYaml.trim() ? manifestYaml : null,
        overwrite,
      });
      if (data?.ok) {
        setSuccess(data.message || 'Plugin files written. Restart the API, then refresh the plugin list.');
        onInstalled();
      } else {
        setError('Unexpected response from server.');
      }
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.data) {
        const d = e.response.data as { detail?: string | { msg: string }[] };
        if (typeof d.detail === 'string') {
          setError(d.detail);
        } else if (Array.isArray(d.detail) && d.detail[0] && 'msg' in d.detail[0]) {
          setError(String((d.detail[0] as { msg: string }).msg));
        } else {
          setError(e.message);
        }
      } else {
        setError('Request failed. Is the API running?');
      }
    } finally {
      setBusy(false);
    }
  };

  const submit = () => {
    if (mode === 'zip') void submitZip();
    else void submitPaste();
  };

  /** Portal to `#ff-overlay-root` (see index.html / index.css) so we sit above layout chrome, not under `main` z-0. */
  const shell = (
    <div
      className="flex h-[100dvh] min-h-0 w-full flex-col bg-canvas-cream"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
    >
      <div className="shrink-0 px-4 pb-2 pt-[max(0.75rem,env(safe-area-inset-top))] md:px-8 md:pb-3 md:pt-6">
        <div
          className={[
            'mx-auto flex max-w-3xl min-h-14 items-center justify-between gap-3 rounded-2xl border border-ink-black/10',
            'bg-white/90 px-4 py-3 backdrop-blur-md shadow-[0px_8px_32px_rgba(0,0,0,0.1)]',
            'sm:min-h-16 sm:rounded-[999px] sm:px-5 sm:py-3 sm:shadow-[0px_4px_28px_rgba(0,0,0,0.08)]',
          ].join(' ')}
        >
          <h2 id={titleId} className="text-lg font-medium pr-2 md:text-xl">
            Add your plugin
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 flex h-11 w-11 items-center justify-center rounded-full border border-ink-black/20 text-lg leading-none hover:bg-ink-black/5"
            aria-label="Close"
          >
            ×
          </button>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-4 py-5 sm:px-6 md:px-10">
        <div className="mx-auto max-w-3xl space-y-4 text-sm text-ink-black/85">
          <p className="text-ink-black/70">
            Writes to <code className="text-xs bg-ink-black/5 px-1 rounded">plugins/&lt;id&gt;/</code> on the server
            that hosts the API. You must <strong>restart the API</strong> after a successful install.
          </p>
          <div className="flex flex-wrap gap-2" role="tablist" aria-label="Install method">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'zip'}
              onClick={() => {
                setMode('zip');
                setError(null);
                setSuccess(null);
              }}
              className={[
                'rounded-full px-4 py-2 text-sm font-medium border-2 transition-colors',
                mode === 'zip'
                  ? 'bg-ink-black text-canvas-cream border-ink-black'
                  : 'bg-white/80 text-ink-black/80 border-ink-black/15',
              ].join(' ')}
            >
              Upload .zip (marketplace)
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'paste'}
              onClick={() => {
                setMode('paste');
                setError(null);
                setSuccess(null);
              }}
              className={[
                'rounded-full px-4 py-2 text-sm font-medium border-2 transition-colors',
                mode === 'paste'
                  ? 'bg-ink-black text-canvas-cream border-ink-black'
                  : 'bg-white/80 text-ink-black/80 border-ink-black/15',
              ].join(' ')}
            >
              Paste code
            </button>
          </div>

          {mode === 'zip' ? (
            <>
              <div>
                <span className="text-xs font-bold tracking-wide uppercase text-ink-black/50">Plugin bundle (.zip)</span>
                <div className="mt-1 flex flex-wrap gap-2">
                  <input
                    ref={zipRef}
                    type="file"
                    accept=".zip,application/zip"
                    className="sr-only"
                    onChange={onPickZip}
                  />
                  <button
                    type="button"
                    onClick={() => zipRef.current?.click()}
                    className="pill-button-secondary text-sm py-1.5 px-3"
                  >
                    Choose .zip
                  </button>
                  {zipFile && (
                    <span className="text-sm text-ink-black/70 self-center">{zipFile.name}</span>
                  )}
                </div>
                <p className="mt-2 text-xs text-ink-black/55">
                  Download a <code className="text-[11px]">.ffplugin.zip</code> from the public marketplace, then upload
                  it here. The archive must contain exactly one top-level folder with{' '}
                  <code className="text-[11px]">logic.py</code> and <code className="text-[11px]">manifest.yaml</code>.
                </p>
              </div>
            </>
          ) : (
            <>
              <label className="block">
                <span className="text-xs font-bold tracking-wide uppercase text-ink-black/50">
                  Plugin id (folder name)
                </span>
                <input
                  className="mt-1 w-full border border-ink-black/20 rounded-xl px-3 py-2"
                  value={pluginId}
                  onChange={(e) => setPluginId(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
                  placeholder="e.g. my_reports"
                  autoComplete="off"
                />
              </label>
              <div>
                <span className="text-xs font-bold tracking-wide uppercase text-ink-black/50">logic.py</span>
                <div className="mt-1 flex flex-wrap gap-2">
                  <input ref={fileRef} type="file" accept=".py,text/x-python" className="sr-only" onChange={onPickFile} />
                  <button
                    type="button"
                    onClick={() => fileRef.current?.click()}
                    className="pill-button-secondary text-sm py-1.5 px-3"
                  >
                    Choose .py file
                  </button>
                </div>
                <textarea
                  className="mt-2 w-full min-h-[200px] sm:min-h-[min(50vh,420px)] font-mono text-xs border border-ink-black/20 rounded-xl p-3"
                  value={logicPy}
                  onChange={(e) => {
                    setLogicPy(e.target.value);
                    setError(null);
                  }}
                  placeholder="Or paste your logic.py here (must include router = APIRouter())"
                  spellCheck={false}
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="rounded border-ink-black/30"
                  checked={useCustomManifest}
                  onChange={(e) => setUseCustomManifest(e.target.checked)}
                />
                <span>Provide custom manifest.yaml (otherwise a default is generated from the plugin id)</span>
              </label>
              {useCustomManifest && (
                <label className="block">
                  <span className="text-xs font-bold tracking-wide uppercase text-ink-black/50">manifest.yaml</span>
                  <textarea
                    className="mt-1 w-full min-h-[100px] font-mono text-xs border border-ink-black/20 rounded-xl p-3"
                    value={manifestYaml}
                    onChange={(e) => setManifestYaml(e.target.value)}
                    placeholder={'name: "My Plugin"\ndescription: "..."\nversion: "1.0.0"'}
                    spellCheck={false}
                  />
                </label>
              )}
            </>
          )}

          <label className="flex items-center gap-2 cursor-pointer text-ink-black/80">
            <input
              type="checkbox"
              className="rounded border-ink-black/30"
              checked={overwrite}
              onChange={(e) => setOverwrite(e.target.checked)}
            />
            <span>Overwrite if this plugin id already exists on the server</span>
          </label>
          {error && <p className="text-signal-orange text-sm">{error}</p>}
          {success && <p className="text-emerald-800 text-sm whitespace-pre-wrap">{success}</p>}
        </div>
      </div>
      <div className="shrink-0 px-4 pt-3 pb-[max(1rem,env(safe-area-inset-bottom))] md:px-8 md:pb-8">
        <div
          className={[
            'mx-auto flex max-w-3xl flex-col-reverse gap-2 rounded-2xl border border-ink-black/10',
            'bg-white/90 px-4 py-3 backdrop-blur-md shadow-[0px_8px_32px_rgba(0,0,0,0.1)]',
            'sm:flex-row sm:items-center sm:justify-end sm:rounded-[999px] sm:px-5 sm:py-3 sm:shadow-[0px_4px_28px_rgba(0,0,0,0.08)]',
          ].join(' ')}
        >
          <button type="button" onClick={onClose} className="pill-button-secondary w-full sm:w-auto">
            {success ? 'Close' : 'Cancel'}
          </button>
          {!success && (
            <button
              type="button"
              disabled={busy}
              onClick={() => void submit()}
              className="pill-button w-full sm:w-auto disabled:opacity-50"
            >
              {busy ? 'Installing…' : mode === 'zip' ? 'Install from .zip' : 'Install plugin'}
            </button>
          )}
        </div>
      </div>
    </div>
  );

  if (typeof document === 'undefined') return null;
  return createPortal(shell, overlayMountEl());
}
