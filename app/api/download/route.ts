// The shortcut file, only for a browser that has signed in with publik (the builds hub's listing).
import { cookies } from "next/headers";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { gateStatus } from "@/kit/ai/publik";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const FILE = "Camera Roll Detox.shortcut";

export async function GET(req: Request) {
  const s = await gateStatus(await cookies(), req, { provision: false });
  const signedIn = s.state === "ready" || s.state === "choose" || s.state === "pending";
  if (!signedIn) return Response.json({ error: "Sign in with publik first." }, { status: 401 });
  const file = await readFile(join(process.cwd(), "shortcut", "dist", FILE));
  return new Response(new Uint8Array(file), {
    headers: {
      "content-type": "application/octet-stream",
      "content-disposition": `attachment; filename="${FILE}"`,
      "cache-control": "no-store",
    },
  });
}
