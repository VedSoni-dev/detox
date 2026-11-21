"use client";
// Sign in with publik in front of /app (every studio build signs in through the builds hub's publik listing). The
// landing at "/" stays open. The site runs no AI itself, so signed in is enough (usesAi: false). Once open, the
// download page renders inside <StudioProvider>, which counts usage for the builds hub and publik.
import Link from "next/link";
import type { ReactNode } from "react";
import { StudioProvider } from "@/kit/react/studio";
import { usePublikGate } from "@/kit/react/gate";
import type { GateAction } from "@/kit/ai/publik"; // types only
import { Logo } from "@/components/Logo";
import config from "@/studio.config";

export function Gate({ children }: { children: ReactNode }) {
  const g = usePublikGate({ usesAi: false });
  if (g.open) return <StudioProvider>{children}</StudioProvider>;

  const shown = g.shown;
  const asking = g.signingIn || g.loading;
  const title = asking ? "Sign in to get the shortcut" : shown?.screen.title ?? "Sign in with publik";
  const body = asking
    ? "Camera Roll Detox is free. Sign in with publik once and the download unlocks on this browser."
    : shown?.screen.body ?? "";

  return (
    <div className="min-h-dvh bg-bg">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-2 sm:px-6">
          <Link href="/" className="flex min-h-11 items-center gap-2 font-display text-lg font-semibold tracking-tight"><Logo />{config.app.name}</Link>
          <a href={config.app.repo} target="_blank" rel="noopener noreferrer" className="flex min-h-11 items-center text-sm text-muted transition-colors duration-150 hover:text-fg">Open source</a>
        </div>
      </header>
      <main className="mx-auto max-w-xl px-4 pb-24 pt-14 sm:px-6 sm:pt-24" aria-busy={g.busy}>
        <section className="sk-stagger">
          <h1 className="text-4xl leading-[1.05] sm:text-5xl">{title}</h1>
          <p className="mt-5 text-lg leading-relaxed text-muted">{body}</p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            {g.loading && <span className="sk-btn inline-flex items-center opacity-70" aria-label="Loading"><span className="sk-spinner" aria-hidden /></span>}
            {g.needsInstall && <button type="button" className="sk-btn !min-h-12" disabled={g.busy} onClick={() => void g.provision()}>Sign in with publik</button>}
            {shown?.screen.buttons.map((b, i) => <GateButton key={b.action} action={b.action} label={b.label} primary={i === 0} href={g.hrefFor(b.action)} busy={g.busy} onAct={g.act} />)}
          </div>
          {g.note && (
            <p className="mt-5 flex items-center gap-2.5 text-sm text-muted" role="status">
              {g.waiting && <span className="sk-spinner" aria-hidden />}
              {g.note}
            </p>
          )}
          {g.signingIn && <p className="mt-5 text-sm text-muted">publik opens in a new tab. Come back here once you&rsquo;re signed in.</p>}
          <noscript><p className="mt-5 text-sm text-muted">Turn on JavaScript to sign in with publik.</p></noscript>
          <ul className="mt-10 grid gap-2 border-t border-line pt-6 text-sm text-muted">
            <li>Open this page on your iPhone, in Safari. The shortcut installs there.</li>
            <li>A free alternative to {config.app.alternativeTo}. Open source, MIT.</li>
            <li>Signing in through <a href="https://publikhq.com" target="_blank" rel="noopener noreferrer" className="text-fg underline decoration-line underline-offset-4 hover:decoration-fg">publik</a> keeps it free.</li>
          </ul>
        </section>
      </main>
    </div>
  );
}

function GateButton({ action, label, primary, href, busy, onAct }: { action: GateAction; label: string; primary: boolean; href: string | null; busy: boolean; onAct: (a: GateAction) => Promise<void> }) {
  const cls = `sk-btn !min-h-12 ${primary ? "" : "sk-btn-quiet"}`;
  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={`${cls} inline-flex items-center`}
        onClick={() => void onAct(action)} onAuxClick={(e) => { if (e.button === 1) void onAct(action); }}>{label}</a>
    );
  }
  return <button type="button" className={cls} disabled={busy} onClick={() => void onAct(action)}>{label}</button>;
}
