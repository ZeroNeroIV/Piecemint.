import { BookOpen, LayoutDashboard } from 'lucide-react';

import { MAIN_APP_URL } from './lib/urls';

export default function ForDevelopers() {
  const appPluginsUrl = `${MAIN_APP_URL}/library`;

  return (
    <div className="space-y-12 max-w-3xl pb-16 pt-12">
      <header>
        <div className="flex items-start gap-3">
          <BookOpen className="shrink-0 text-ink-black/50 mt-1" size={28} aria-hidden />
          <div>
            <h1 className="text-[48px] leading-none tracking-tight mb-4">Build your own plugin</h1>
            <p className="text-ink-black/70 text-lg">
              How Piecemint discovers modules under <code className="text-sm bg-ink-black/5 px-1.5 py-0.5 rounded">plugins/</code> and
              exposes them in the app. Add an optional <code className="text-xs bg-ink-black/5 px-1 rounded">icon:</code> field in{' '}
              <code className="text-xs">manifest.yaml</code> pointing to an image in the plugin folder (e.g.{' '}
              <code className="text-xs">icon.svg</code>) — it appears in the Piecemint sidebar, plugin library, search, and on this
              marketplace. Plugin cards and <strong>Download for Piecemint</strong> zips mirror the same folders under{' '}
              <code className="text-sm bg-ink-black/5 px-1.5 py-0.5 rounded">piecemint/backend/plugins/</code> and{' '}
              <code className="text-sm bg-ink-black/5 px-1.5 py-0.5 rounded">disabled_plugins/</code> (not stubs). Optional{' '}
              <code className="text-xs bg-ink-black/5 px-1 rounded">marketplace:</code> block in <code className="text-xs">manifest.yaml</code> can
              set display-only <code className="text-xs">price</code> / <code className="text-xs">is_free</code>.
            </p>
          </div>
        </div>
        <div className="mt-8 flex flex-col sm:flex-row flex-wrap gap-4">
          <a
            href={appPluginsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="pill-button inline-flex items-center justify-center gap-2 no-underline w-full sm:w-auto"
          >
            <LayoutDashboard size={18} aria-hidden />
            Open Piecemint — install plugins
          </a>
          <p className="text-sm text-ink-black/60 self-center">
            Bundles from this site are imported in the main app under <strong>Add your plugin → Upload .zip</strong>.
          </p>
        </div>
      </header>

      <section className="space-y-4 pt-6">
        <h2 className="text-xl font-medium tracking-tight">1. Folder layout</h2>
        <p className="text-ink-black/80">
          Each plugin is a directory next to the backend code, for example{' '}
          <code className="text-sm bg-ink-black/5 px-1.5 py-0.5 rounded">piecemint/backend/plugins/my_plugin/</code>.
          Typical pieces:
        </p>
        <ul className="list-disc pl-6 space-y-2 text-ink-black/80">
          <li>
            <strong>manifest.yaml</strong> — required for discovery. Metadata: <code className="text-xs">name</code>,{' '}
            <code className="text-xs">description</code>, <code className="text-xs">version</code>; optional{' '}
            <code className="text-xs">icon</code> for a logo file in this folder (svg, png, webp, jpeg, gif, or ico).
          </li>
          <li>
            <strong>logic.py</strong> — defines a FastAPI <code className="text-xs">router</code> for HTTP under{' '}
            <code className="text-xs">/api/plugins</code>. Omit only for rare MCP-only plugins; most bundles include this file.
          </li>
          <li>
            <strong>mcp_extras.py</strong> (optional) — extends the Piecemint MCP server; see section 6.
          </li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium tracking-tight">2. manifest.yaml</h2>
        <pre className="text-sm bg-ink-black/5 p-4 rounded-[20px] overflow-x-auto border border-ink-black/10">
{`name: "My Plugin"
description: "What it does in one line."
version: "1.0.0"
icon: "icon.svg"   # optional; path under this folder`}
        </pre>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium tracking-tight">3. logic.py and routes</h2>
        <p className="text-ink-black/80">
          Import <code className="text-xs bg-ink-black/5 px-1 rounded">APIRouter</code> from FastAPI, create{' '}
          <code className="text-xs bg-ink-black/5 px-1 rounded">router = APIRouter()</code>, and register paths. The
          plugin manager mounts your router under the prefix{' '}
          <code className="text-xs bg-ink-black/5 px-1 rounded">/api/plugins</code>, so a route like{' '}
          <code className="text-xs">@router.get("/my_plugin/hello")</code> is served at{' '}
          <code className="text-xs">/api/plugins/my_plugin/hello</code>.
        </p>
        <pre className="text-sm bg-ink-black/5 p-4 rounded-[20px] overflow-x-auto border border-ink-black/10">
{`from fastapi import APIRouter

router = APIRouter()

@router.get("/my_plugin/hello")
def hello():
    return {"message": "Hello from my plugin"}`}
        </pre>
        <p className="text-ink-black/70 text-sm">
          You can use shared app modules (e.g. database) by importing from the backend package the same way existing
          plugins do; keep imports stable when you upgrade Piecemint.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium tracking-tight">4. Enable in the UI</h2>
        <p className="text-ink-black/80">
          After files are on disk, restart the API process so routes are registered. Open{' '}
          <strong>Plugin library</strong> and use <strong>Refresh plugin list</strong>. Turn the plugin on with the
          switch; it appears in the sidebar when enabled.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium tracking-tight">5. Add your plugin from the Piecemint app</h2>
        <p className="text-ink-black/80">
          In the <strong>Plugin library</strong> page inside Piecemint, <strong>Add your plugin</strong> can write files to{' '}
          <code className="text-xs">plugins/&lt;id&gt;/</code> on the machine running the <em>Piecemint</em> API, or you can upload a{' '}
          <code className="text-xs">.ffplugin.zip</code> downloaded from this marketplace. For production, set{' '}
          <code className="text-xs">FF_DISABLE_PLUGIN_UPLOAD=1</code> on the server to disable uploads. Always restart the API after installing.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium tracking-tight">6. Optional: Piecemint MCP (<code className="text-base">mcp_extras.py</code>)</h2>
        <p className="text-ink-black/80">
          <code className="text-xs bg-ink-black/5 px-1 rounded">piecemint/backend/mcp_server.py</code> loads optional{' '}
          <code className="text-xs">plugins/&lt;id&gt;/mcp_extras.py</code> after built-in tools. The module must define{' '}
          <code className="text-xs">register_mcp(mcp)</code> and use the same <code className="text-xs">manifest.yaml</code> gate as
          HTTP plugins. Folders under <code className="text-xs">disabled_plugins/</code> are ignored. Restart the MCP host after
          changes. The <code className="text-xs">email_and_invoice_capabilities</code> tool reports{' '}
          <code className="text-xs">plugin_mcp_extras_loaded</code> for debugging.
        </p>
        <pre className="text-sm bg-ink-black/5 p-4 rounded-[20px] overflow-x-auto border border-ink-black/10">
{`# plugins/my_plugin/mcp_extras.py

def register_mcp(mcp) -> None:
    @mcp.tool()
    def my_plugin_status() -> str:
        return '{"ok": true, "plugin": "my_plugin"}'`}
        </pre>
        <p className="text-ink-black/70 text-sm">
          Same import rules as <code className="text-xs">logic.py</code>; run MCP from <code className="text-xs">piecemint/backend</code>. For
          database access, copy ORM field values while the SQLAlchemy session is open before returning from a tool handler.
        </p>
      </section>

      <p className="text-sm text-ink-black/55">
        Reference: see existing plugins under <code className="text-xs">backend/plugins/</code> in this repository for
        full examples (e.g. tax calculator, invoice generator). In Piecemint open <strong>Plugin library → How to build a plugin</strong>{' '}
        for the in-app mirror of this guide.
      </p>
    </div>
  );
}
