// One file says what this build is and which AI modes it offers. The kit reads it everywhere.
import type { StudioConfig } from "@/kit/ai/types";

const config: StudioConfig = {
  app: {
    name: "Camera Roll Detox",
    slug: "detox",
    version: "0.1.0",
    tagline: "Clean your iPhone camera roll with AI in one tap, free",
    repo: "https://github.com/VedSoni-dev/detox",
    url: "https://detox.vedantsoni.com",
    alternativeTo: "Cleanup",
  },
  // Pick the modes that make sense for this build (docs/auth.md). Order = order in the picker. The hosted picker hides ChatGPT plan (local runs only).
  modes: ["publik"],
  defaultMode: "publik",
};

export default config;
