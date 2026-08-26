interface AircraftIconProps {
  className?: string
}

// Original geometric top-down aircraft silhouette (single closed polygon,
// symmetric left/right), not sourced from any icon library or emoji.
export function AircraftIcon({ className }: AircraftIconProps) {
  return (
    <svg viewBox="0 0 100 100" className={className} fill="currentColor" aria-hidden="true">
      <polygon points="50,2 54,40 98,62 54,52 54,78 68,92 50,84 32,92 46,78 46,52 2,62 46,40" />
    </svg>
  )
}
