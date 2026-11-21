// A camera-roll grid with one tile cleared. Own mark, no one else's.
export function Logo({ size = 22 }: { size?: number }) {
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} aria-hidden>
      <rect x="2" y="2" width="20" height="20" rx="6" fill="var(--accent)" />
      <rect x="6" y="6" width="5" height="5" rx="1.4" fill="#fff" />
      <rect x="13" y="6" width="5" height="5" rx="1.4" fill="#fff" />
      <rect x="6" y="13" width="5" height="5" rx="1.4" fill="#fff" />
      <rect x="13" y="13" width="5" height="5" rx="1.4" fill="none" stroke="#fff" strokeWidth="1.4" strokeDasharray="2 1.6" />
    </svg>
  );
}
