// The public landing page at "/": what it is, the real product, and how to get it. Nobody signs in to see this.
import Link from "next/link";
import { existsSync } from "node:fs";
import { join } from "node:path";
import config from "@/studio.config";
import { Logo } from "@/components/Logo";

const ASKS = [
  { q: "What's eating your storage?", a: "Old screenshots, long videos, blurry and junk photos, everything, or just tell it in your own words." },
  { q: "Keep screenshots from the last…", a: "A week, a month, three months, or clear them all. Favorites are skipped." },
  { q: "Which videos can go?", a: "It lists your longest videos and you pick. Nothing long gets deleted sight unseen." },
  { q: "Found 412 screenshots, 9 videos, 63 junk photos. Delete 484?", a: "Then iOS asks one last time. Everything goes to Recently Deleted for 30 days." },
];

const AI = [
  { t: "Apple Intelligence", d: "Free, on your iPhone 15 Pro or newer." },
  { t: "Sign in with publik", d: "One tap from inside the shortcut. Works on any iPhone." },
  { t: "Your own key", d: "Paste an OpenRouter, Gemini, Anthropic, OpenAI or publik key. It picks the right one." },
  { t: "No AI", d: "Skip it. Screenshots and long videos still get cleaned." },
];

export default function Landing() {
  const { app } = config;
  const hero = existsSync(join(process.cwd(), "public/hero.png"));
  return (
    <main className="relative isolate overflow-hidden">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
        <Link href="/" className="flex min-h-11 items-center gap-2 font-display text-lg font-semibold"><Logo />{app.name}</Link>
        <div className="flex items-center gap-2">
          <a href={app.repo} className="sk-btn sk-btn-quiet hidden sm:inline-flex" target="_blank" rel="noopener noreferrer">GitHub</a>
          <Link href="/app" className="sk-btn">Get it free</Link>
        </div>
      </nav>

      <section className="relative mx-auto grid max-w-6xl gap-12 px-5 pb-16 pt-14 sm:px-8 sm:pt-24 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div className="sk-stagger max-w-2xl">
          <p className="font-mono text-xs uppercase tracking-widest text-muted">Free, open-source alternative to {app.alternativeTo}</p>
          <h1 className="mt-4 text-5xl font-semibold leading-[0.95] sm:text-7xl">Your camera roll, cleaned in one tap.</h1>
          <p className="mt-6 max-w-xl text-lg text-muted">An Apple Shortcut that asks what&rsquo;s eating your storage, finds old screenshots, long videos and blurry junk photos, and clears them all with one iOS confirmation. No app, no subscription.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/app" className="sk-btn !min-h-12">Get the shortcut →</Link>
            <a href={app.repo} className="sk-btn sk-btn-quiet !min-h-12" target="_blank" rel="noopener noreferrer">Read the source</a>
          </div>
          <p className="mt-4 text-sm text-muted">iPhone only. Sign in with publik to download.</p>
        </div>
        {hero && (
          <div className="sk-rise mx-auto w-full max-w-[320px] overflow-hidden rounded-[36px] border border-line bg-card shadow-[var(--shadow-3)]" style={{ animationDelay: "160ms" }}>
            {/* The real shortcut on a real iPhone (iPhone Mirroring capture), never a mockup. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/hero.png" alt="Camera Roll Detox asking what's eating your storage, on an iPhone" className="block w-full" />
          </div>
        )}
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
        <h2 className="text-3xl font-semibold sm:text-4xl">It asks, you pick, it cleans</h2>
        <p className="mt-3 max-w-xl text-muted">A few quick questions, only for what you chose. Then one summary and one delete.</p>
        <ol className="mt-8 grid gap-3 sm:grid-cols-2">
          {ASKS.map((s, i) => (
            <li key={s.q} className="rounded-[var(--radius)] border border-line bg-card p-5 shadow-[var(--shadow-1)]">
              <span className="font-mono text-xs text-muted">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="mt-2 text-lg font-semibold">&ldquo;{s.q}&rdquo;</h3>
              <p className="mt-1 text-sm text-muted">{s.a}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
        <h2 className="text-3xl font-semibold sm:text-4xl">The AI looks at your photos, you choose which AI</h2>
        <p className="mt-3 max-w-xl text-muted">For blurry, accidental and one-time photos (pocket shots, receipts, parking spots), each recent photo gets a quick look. If it&rsquo;s unsure, it keeps the photo.</p>
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {AI.map((m) => (
            <div key={m.t} className="rounded-[var(--radius)] border border-line bg-card p-5 shadow-[var(--shadow-1)]">
              <h3 className="text-lg font-semibold">{m.t}</h3>
              <p className="mt-1 text-sm text-muted">{m.d}</p>
            </div>
          ))}
        </div>
        <p className="mt-6 max-w-2xl text-sm text-muted">With Apple Intelligence nothing leaves Apple. With publik or your own key, a small 512px copy of each checked photo goes to that service and nowhere else. Screenshots and videos are found on the phone, no AI involved.</p>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
        <h2 className="text-3xl font-semibold sm:text-4xl">Open source. Read every step.</h2>
        <p className="mt-3 max-w-xl text-muted">MIT licensed. Shortcuts shows you every action before you add it, and the generator that builds the file is on GitHub.</p>
        <pre className="mt-6 overflow-x-auto rounded-[var(--radius-sm)] border border-line bg-bg-2 p-4 font-mono text-sm">{`git clone ${app.repo}.git && cd ${app.slug}/shortcut && python3 build.py`}</pre>
      </section>

      <footer className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-8 text-sm text-muted sm:px-8">
        <span>Built by Vedant Soni · <a className="underline underline-offset-4" href="https://instagram.com/vedanttalksai" target="_blank" rel="noopener noreferrer">@vedanttalksai</a> · Not affiliated with {app.alternativeTo}.</span>
        <a className="underline underline-offset-4" href={app.repo} target="_blank" rel="noopener noreferrer">Source on GitHub</a>
      </footer>
    </main>
  );
}
