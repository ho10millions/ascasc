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
      {/* Outer glow ring */}
      <circle cx="50" cy="50" r="46" stroke="url(#logo-gradient)" strokeWidth="2" opacity="0.6" />
      <circle cx="50" cy="50" r="42" stroke="url(#logo-gradient)" strokeWidth="1" opacity="0.3" />

      {/* Inner hexagonal shape */}
      <path
        d="M50 8 L85 28 L85 72 L50 92 L15 72 L15 28 Z"
        fill="url(#logo-bg)"
        stroke="url(#logo-gradient)"
        strokeWidth="1.5"
        opacity="0.9"
      />

      {/* Dollar sign — stylized */}
      <path
        d="M50 25 L50 75"
        stroke="url(#logo-gradient)"
        strokeWidth="2.5"
        strokeLinecap="round"
        opacity="0.8"
      />
      <path
        d="M62 35 C62 35 58 30 50 30 C42 30 37 34 37 39 C37 44 42 47 50 49 C58 51 63 54 63 60 C63 66 58 70 50 70 C42 70 38 65 38 65"
        stroke="url(#logo-gradient)"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />

      {/* Steam-like circles (controller/joystick hint) */}
      <circle cx="33" cy="45" r="4" fill="url(#logo-gradient)" opacity="0.4" />
      <circle cx="67" cy="55" r="4" fill="url(#logo-gradient)" opacity="0.4" />

      {/* Small accent dots */}
      <circle cx="50" cy="22" r="2" fill="#22d3ee" opacity="0.9" />
      <circle cx="50" cy="78" r="2" fill="#a78bfa" opacity="0.9" />

      {/* Gradients */}
      <defs>
        <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#22d3ee" />
          <stop offset="50%" stopColor="#06b6d4" />
          <stop offset="100%" stopColor="#a78bfa" />
        </linearGradient>
        <linearGradient id="logo-bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgba(6, 182, 212, 0.15)" />
          <stop offset="100%" stopColor="rgba(167, 139, 250, 0.08)" />
        </linearGradient>
      </defs>
    </svg>
  );
}
