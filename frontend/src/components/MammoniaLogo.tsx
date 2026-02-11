export default function MammoniaLogo({ size = 40, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="logo-gold" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#f5d475" />
          <stop offset="50%" stopColor="#d4a844" />
          <stop offset="100%" stopColor="#b8860b" />
        </linearGradient>
        <linearGradient id="logo-gold-light" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#fce8a6" />
          <stop offset="100%" stopColor="#d4a844" />
        </linearGradient>
        <linearGradient id="logo-bg-fill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0c1220" />
          <stop offset="100%" stopColor="#0a0e1a" />
        </linearGradient>
      </defs>

      {/* Shield / diamond shape — premium feel */}
      <path
        d="M50 4 L90 25 L90 65 L50 96 L10 65 L10 25 Z"
        fill="url(#logo-bg-fill)"
        stroke="url(#logo-gold)"
        strokeWidth="2.5"
      />

      {/* Inner border line — double frame like luxury brands */}
      <path
        d="M50 12 L83 29 L83 63 L50 88 L17 63 L17 29 Z"
        fill="none"
        stroke="url(#logo-gold)"
        strokeWidth="0.8"
        opacity="0.5"
      />

      {/* Bold M letter — Mammonia monogram */}
      <path
        d="M30 68 L30 35 L42 55 L50 42 L58 55 L70 35 L70 68"
        stroke="url(#logo-gold-light)"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />

      {/* Small diamond accent at top */}
      <path
        d="M50 16 L53 20 L50 24 L47 20 Z"
        fill="url(#logo-gold)"
        opacity="0.8"
      />
    </svg>
  );
}
