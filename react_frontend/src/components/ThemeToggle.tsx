interface ThemeToggleProps {
  theme: 'dark' | 'light'
  onToggle: () => void
}

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="12" cy="12" r="4.5" />
          <line x1="12" y1="1.5" x2="12" y2="4.5" />
          <line x1="12" y1="19.5" x2="12" y2="22.5" />
          <line x1="1.5" y1="12" x2="4.5" y2="12" />
          <line x1="19.5" y1="12" x2="22.5" y2="12" />
          <line x1="4.4" y1="4.4" x2="6.5" y2="6.5" />
          <line x1="17.5" y1="17.5" x2="19.6" y2="19.6" />
          <line x1="4.4" y1="19.6" x2="6.5" y2="17.5" />
          <line x1="17.5" y1="6.5" x2="19.6" y2="4.4" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M20.5 14.7A8.5 8.5 0 0 1 9.3 3.5a.6.6 0 0 0-.8-.8 9.7 9.7 0 1 0 12.8 12.8.6.6 0 0 0-.8-.8Z" />
        </svg>
      )}
    </button>
  )
}
