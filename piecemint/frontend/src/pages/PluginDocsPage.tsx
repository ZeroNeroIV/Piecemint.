import { Link } from 'react-router-dom';
import { ArrowLeft, BookOpen } from 'lucide-react';

export default function PluginDocsPage() {
  return (
    <div className="w-full max-w-5xl space-y-10 pb-16">
      <header>
        <Link
          to="/library"
          className="inline-flex items-center gap-2 text-sm font-medium text-signal-orange hover:underline underline-offset-2 mb-6"
        >
          <ArrowLeft size={16} aria-hidden />
          Back to plugin library
        </Link>
        <div className="flex items-start gap-3">
          <BookOpen className="shrink-0 text-ink-black/50 mt-1" size={28} aria-hidden />
          <div>
            <h1 className="text-3xl md:text-4xl font-medium tracking-tight mb-2">Build your own plugin</h1>
            <p className="text-ink-black/70 text-lg">
              How Piecemint discovers modules under <code className="text-sm bg-ink-black/5 px-1.5 py-0.5 rounded">plugins/</code> and
              exposes them in the app.
            </p>
          </div>
        </div>
      </header>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">1. Folder layout</h2>
        <p className="text-ink-black/80">
          Each plugin is a directory next to the backend code, for example{' '}
          <code className="text-sm bg-ink-black/5 px-1.5 py-0.5 rounded">piecemint/backend/plugins/my_plugin/</code>.
          Typical pieces:
        </p>
        <ul className="list-disc pl-6 space-y-2 text-ink-black/80">
          <li>
            <strong>manifest.yaml</strong> — required for discovery. Metadata: <code className="text-xs">name</code>,{' '}
            <code className="text-xs">description</code>, <code className="text-xs">version</code>, and optional{' '}
            <code className="text-xs">icon</code> (path to an image under the plugin folder; shown in the app sidebar,
            plugin library, global search, and on the marketplace site).
          </li>
          <li>
            <strong>logic.py</strong> — defines a FastAPI <code className="text-xs">router</code> for HTTP routes under{' '}
            <code className="text-xs">/api/plugins</code>. Skip only if the plugin is MCP-only (unusual); most plugins
            include this file.
          </li>
          <li>
            <strong>mcp_extras.py</strong> (optional) — extends the Piecemint MCP server with extra tools; see section 6.
          </li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">2. manifest.yaml</h2>
        <pre className="text-sm bg-ink-black/5 p-4 rounded-2xl overflow-x-auto border border-ink-black/10">
{`name: "My Plugin"
description: "What it does in one line."
version: "1.0.0"
icon: "icon.svg"   # optional; .svg, .png, .webp, .jpg, .gif, or .ico — stays inside this folder`}
        </pre>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">3. logic.py and routes</h2>
        <p className="text-ink-black/80">
          Import <code className="text-xs bg-ink-black/5 px-1 rounded">APIRouter</code> from FastAPI, create{' '}
          <code className="text-xs bg-ink-black/5 px-1 rounded">router = APIRouter()</code>, and register paths. The
          plugin manager mounts your router under the prefix{' '}
          <code className="text-xs bg-ink-black/5 px-1 rounded">/api/plugins</code>, so a route like{' '}
          <code className="text-xs">@router.get(&quot;/my_plugin/hello&quot;)</code> is served at{' '}
          <code className="text-xs">/api/plugins/my_plugin/hello</code>.
        </p>
        <pre className="text-sm bg-ink-black/5 p-4 rounded-2xl overflow-x-auto border border-ink-black/10">
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
        <h2 className="text-xl font-medium">4. Enable in the UI</h2>
        <p className="text-ink-black/80">
          After files are on disk, restart the API process so routes are registered. Open{' '}
          <strong>Plugin library</strong> and use <strong>Refresh plugin list</strong>. Turn the plugin on with the
          switch; it appears in the sidebar when enabled.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">5. Add your plugin from the app</h2>
        <p className="text-ink-black/80">
          On the plugin library page, <strong>Add your plugin</strong> can write <code className="text-xs">logic.py</code> and
          a generated or pasted <code className="text-xs">manifest.yaml</code> into <code className="text-xs">plugins/&lt;id&gt;/</code> on
          the machine running the API. For production, set <code className="text-xs">FF_DISABLE_PLUGIN_UPLOAD=1</code> on the server
          to disable this. Always restart the API after installing.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-medium">6. Optional: Piecemint MCP (<code className="text-base">mcp_extras.py</code>)</h2>
        <p className="text-ink-black/80">
          The stdio MCP entrypoint <code className="text-xs bg-ink-black/5 px-1 rounded">piecemint/backend/mcp_server.py</code>{' '}
          loads built-in tools, then calls <code className="text-xs bg-ink-black/5 px-1 rounded">PluginManager.apply_mcp_extras(mcp)</code>.
          For each enabled plugin under <code className="text-xs">plugins/</code> that has a{' '}
          <code className="text-xs">manifest.yaml</code>, if <code className="text-xs">mcp_extras.py</code> exists and defines a
          callable <code className="text-xs">register_mcp(mcp)</code>, that function runs to register additional tools (e.g.{' '}
          <code className="text-xs">@mcp.tool()</code>). Plugins in <code className="text-xs">disabled_plugins/</code> are not
          scanned. Restart the MCP process after adding or changing <code className="text-xs">mcp_extras.py</code>. Use the
          built-in tool <code className="text-xs">email_and_invoice_capabilities</code> to see which plugin extras loaded (
          <code className="text-xs">plugin_mcp_extras_loaded</code>).
        </p>
        <pre className="text-sm bg-ink-black/5 p-4 rounded-2xl overflow-x-auto border border-ink-black/10">
{`# plugins/my_plugin/mcp_extras.py

def register_mcp(mcp) -> None:
    @mcp.tool()
    def my_plugin_status() -> str:
        return '{"ok": true, "plugin": "my_plugin"}'`}
        </pre>
        <p className="text-ink-black/70 text-sm">
          Import shared code the same way as in <code className="text-xs">logic.py</code> (e.g.{' '}
          <code className="text-xs">from api.database import SessionLocal</code>) with the working directory set to{' '}
          <code className="text-xs">piecemint/backend</code>. For SQLAlchemy rows, read attributes while the session is open,
          then close the session before long-running work—same pattern as core{' '}
          <code className="text-xs">send_invoice_email</code>.
        </p>
      </section>

      <p className="text-sm text-ink-black/55">
        Reference: see existing plugins under <code className="text-xs">backend/plugins/</code> in this repository for
        full examples (e.g. tax calculator, invoice generator).
      </p>
    </div>
  );
}
