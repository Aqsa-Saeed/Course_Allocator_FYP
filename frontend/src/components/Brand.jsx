// Logo tile (same artwork as the favicon). Used by the sidebar and the login screens.
export function BrandMark({ size = 36 }) {
  return (
    <svg className="brand-mark" width={size} height={size} viewBox="0 0 64 64" role="img" aria-label="Course Allocation">
      <defs>
        <linearGradient id="brandGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2b8a76" />
          <stop offset="1" stopColor="#0f3d35" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="14" fill="url(#brandGradient)" />
      <polygon points="32,15 56,27 32,39 8,27" fill="#fff" />
      <path d="M18 33.5v9.2c0 2.6 6.3 6.3 14 6.3s14-3.7 14-6.3v-9.2L32 41z" fill="#fff" fillOpacity=".88" />
      <path d="M52 29v13" stroke="#f2c75c" strokeWidth="3" strokeLinecap="round" />
      <circle cx="52" cy="45" r="3.4" fill="#f2c75c" />
    </svg>
  );
}
