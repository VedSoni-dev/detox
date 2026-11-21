import type { Metadata } from "next";
import { Gate } from "@/components/Gate";

export const metadata: Metadata = { title: "Get the shortcut" };

// Sign in with publik in front of the download; signed in, it renders inside <StudioProvider> (components/Gate.tsx).
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <Gate>{children}</Gate>;
}
