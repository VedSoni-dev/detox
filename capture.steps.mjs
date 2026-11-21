// Drives the real site for tools/capture.mjs (README media, GitHub cover, demo GIF). Fresh browser each run.
// /app sits behind Sign in with publik. Capture against the publik mock (see the studio's /studio skill):
//   node ~/Projects/forkthis/templates/publik-next/dev/mock-publik.mjs
//   PUBLIK_ORIGIN=http://localhost:3124 PUBLIK_APP_TOKEN=pat_localtest npm run dev -- -p 3333
//   node tools/capture.mjs http://localhost:3333 --steps apps/detox/capture.steps.mjs --out apps/detox/docs/media --video
export default async function ({ page, go, wait, shot, scroll }) {
  await go("/");
  await wait(1200);
  await shot("cover", { cover: true });
  await shot("screen-1");
  await scroll(900);
  await wait(800);
  await shot("screen-3");

  await go("/app");
  await wait(1500);
  // Before sign-in the file is refused on the server too.
  const before = await page.evaluate(async () => (await fetch("/api/download")).status);
  if (before !== 401) throw new Error(`/api/download answered ${before} before sign-in, expected 401`);
  await shot("screen-2");
  const p = await page.evaluate(async () => fetch("/api/studio/publik/provision", { method: "POST", headers: { "content-type": "application/json" }, body: "{}" }).then((r) => r.json()));
  if (p.claimUrl) await fetch(p.claimUrl);
  await page.reload();
  await page.getByText("Download the shortcut").waitFor({ timeout: 30000 });
  await wait(900);
  await shot("screen-4");
  const after = await page.evaluate(async () => { const r = await fetch("/api/download"); return { status: r.status, bytes: (await r.arrayBuffer()).byteLength }; });
  if (after.status !== 200 || after.bytes < 10000) throw new Error(`/api/download after sign-in: ${JSON.stringify(after)}`);
  console.log(`download ok: ${after.bytes} bytes`);
}
