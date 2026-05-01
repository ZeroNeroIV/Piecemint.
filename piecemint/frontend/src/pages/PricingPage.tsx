import { Link } from 'react-router-dom';
import { BadgeCheck, Building2, Sparkles } from 'lucide-react';

export default function PricingPage() {
  return (
    <div className="w-full max-w-6xl space-y-12 pb-16">
      <header className="max-w-2xl">
        <h1 className="text-3xl md:text-4xl font-medium tracking-tight mb-3">Prices</h1>
        <p className="text-ink-black/70 text-lg">
          Pick the plan that matches how you use Piecemint. Plugin access depends on tier; paid plugins can be billed
          separately when your plan allows.
        </p>
      </header>

      <div className="grid gap-6 md:gap-8 md:grid-cols-3">
        <article className="card p-6 flex flex-col shadow-none border-ink-black/10">
          <div className="flex items-start gap-3 mb-5">
            <Sparkles className="shrink-0 text-ink-black/45 mt-0.5" size={26} aria-hidden />
            <div>
              <h2 className="text-lg font-semibold text-ink-black">Free</h2>
              <p className="text-2xl font-medium tracking-tight mt-1">$0</p>
              <p className="text-sm text-ink-black/55 mt-0.5">Forever · core workspace</p>
            </div>
          </div>
          <p className="text-sm text-ink-black/75 mb-4">
            Use Piecemint&apos;s core product only: dashboards, budgets, contacts, transactions, alerts, and financial
            settings. No plugin library access.
          </p>
          <ul className="text-sm text-ink-black/80 space-y-2 mb-8 flex-1 list-disc pl-5">
            <li>Overview, cash & analytics, budget & cash flow</li>
            <li>Clients & suppliers, transactions & alerts</li>
            <li>Financial settings & exports</li>
            <li className="text-ink-black/55">Plugins not included</li>
          </ul>
          <p className="text-xs text-ink-black/50">
            Best for trying the product or a single operator who only needs built-in tools.
          </p>
        </article>

        <article className="card p-6 flex flex-col border-ink-black/20 ring-1 ring-ink-black/10 shadow-[0px_8px_32px_rgba(0,0,0,0.06)]">
          <div className="flex items-start gap-3 mb-5">
            <BadgeCheck className="shrink-0 text-signal-orange mt-0.5" size={26} aria-hidden />
            <div>
              <h2 className="text-lg font-semibold text-ink-black">Pro</h2>
              <p className="text-2xl font-medium tracking-tight mt-1">
                $15<span className="text-base font-normal text-ink-black/55"> / month</span>
              </p>
              <p className="text-sm text-ink-black/55 mt-0.5">Plugins unlocked</p>
            </div>
          </div>
          <p className="text-sm text-ink-black/75 mb-4">
            Everything in Free, plus the plugin ecosystem: install every <strong className="font-medium">free</strong>{' '}
            plugin from the library, and subscribe individually to paid plugins whenever you need them.
          </p>
          <ul className="text-sm text-ink-black/80 space-y-2 mb-8 flex-1 list-disc pl-5">
            <li>All core features included in Free</li>
            <li>Free plugins in the Plugin library</li>
            <li>Add paid plugins with separate subscriptions as offered</li>
            <li>Best for teams that want invoices, tax tools, workflows, etc.</li>
          </ul>
          <Link
            to="/library"
            className="pill-button inline-flex justify-center items-center text-center no-underline"
          >
            Browse plugin library
          </Link>
        </article>

        <article className="card p-6 flex flex-col border-ink-black/10">
          <div className="flex items-start gap-3 mb-5">
            <Building2 className="shrink-0 text-ink-black/45 mt-0.5" size={26} aria-hidden />
            <div>
              <h2 className="text-lg font-semibold text-ink-black">Enterprise</h2>
              <p className="text-2xl font-medium tracking-tight mt-1">Custom</p>
              <p className="text-sm text-ink-black/55 mt-0.5">Deployments & terms</p>
            </div>
          </div>
          <p className="text-sm text-ink-black/75 mb-4">
            Self-hosted or private setups, consolidated billing for many seats, SSO, SLA, onboarding, or custom plugins.
            We&apos;ll tailor a quote.
          </p>
          <ul className="text-sm text-ink-black/80 space-y-2 mb-8 flex-1 list-disc pl-5">
            <li>Volume licensing &amp; procurement-friendly terms</li>
            <li>Security review &amp; deployment support</li>
            <li>Priority support path</li>
          </ul>
          <a
            href="mailto:sales@piecemint.app?subject=Piecemint%20Enterprise"
            className="pill-button-secondary inline-flex justify-center items-center text-center no-underline border-ink-black/25"
          >
            Contact us
          </a>
        </article>
      </div>

      <footer className="text-sm text-ink-black/55 max-w-xl">
        <p>
          Prices describe intended packaging; billing and checkout may arrive in-product later. Free tier excludes
          plugin installs; Pro unlocks installs per marketplace rules at purchase time.
        </p>
      </footer>
    </div>
  );
}
