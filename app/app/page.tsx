// The download page at "/app", behind Sign in with publik (app/app/layout.tsx). The file comes from /api/download,
// which checks the same sign-in on the server.
import Link from "next/link";
import { Logo } from "@/components/Logo";
import config from "@/studio.config";

const STEPS = [
  { t: "Download it", d: "Tap the button on your iPhone, in Safari. The file lands in Downloads." },
  { t: "Add it", d: "Open the file. Shortcuts shows every step it runs: scroll to the bottom and tap Add Shortcut. Leave the key as none." },
  { t: "Run it", d: "Open Shortcuts and tap Camera Roll Detox. It asks what to clean, shows you what it found, then asks before deleting." },
];

export default function DownloadPage() {
  return (
    <div className="min-h-dvh bg-bg">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-2 sm:px-6">
          <Link href="/" className="flex min-h-11 items-center gap-2 font-display text-lg font-semibold tracking-tight"><Logo />{config.app.name}</Link>
          <a href={config.app.repo} target="_blank" rel="noopener noreferrer" className="flex min-h-11 items-center text-sm text-muted transition-colors duration-150 hover:text-fg">Open source</a>
        </div>
      </header>
      <main className="mx-auto max-w-xl px-4 pb-24 pt-14 sm:px-6 sm:pt-20">
        <section className="sk-stagger">
          <p className="font-mono text-xs uppercase tracking-widest text-muted">You&rsquo;re in</p>
          <h1 className="mt-3 text-4xl leading-[1.05] sm:text-5xl">Get Camera Roll Detox</h1>
          <p className="mt-5 text-lg leading-relaxed text-muted">An Apple Shortcut for iPhone. Free, no app to install.</p>
          <a href="/api/download" className="sk-btn mt-8 inline-flex !min-h-12 items-center" download>Download the shortcut</a>
          <p className="mt-3 text-sm text-muted">On a computer? Open {config.app.url.replace("https://", "")}/app on your iPhone instead.</p>
        </section>
        <ol className="mt-12 grid gap-3">
          {STEPS.map((s, i) => (
            <li key={s.t} className="flex gap-4 rounded-[var(--radius)] border border-line bg-card p-5 shadow-[var(--shadow-1)]" style={{ animation: `sk-rise var(--dur-3) var(--spring) ${160 + i * 60}ms both` }}>
              <span className="grid size-8 shrink-0 place-items-center rounded-full bg-fg font-mono text-sm text-bg">{i + 1}</span>
              <span><span className="block font-semibold">{s.t}</span><span className="mt-1 block text-sm text-muted">{s.d}</span></span>
            </li>
          ))}
        </ol>
        <p className="mt-10 text-sm text-muted">Anything it deletes sits in Recently Deleted for 30 days. Favorites are never touched.</p>
      </main>
    </div>
  );
}
