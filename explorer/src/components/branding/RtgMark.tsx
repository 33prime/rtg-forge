interface RtgMarkProps {
  className?: string;
  size?: number;
}

export default function RtgMark({ className, size = 32 }: RtgMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Background circle */}
      <circle cx="32" cy="32" r="30" fill="#111113" stroke="#27272a" strokeWidth="1" />
      {/* Star top-left */}
      <path
        d="M18 12l1.5 3.5L23 17l-3.5 1.5L18 22l-1.5-3.5L13 17l3.5-1.5z"
        fill="#16ad7a"
      />
      {/* Star top-right */}
      <path
        d="M46 8l1 2.5 2.5 1-2.5 1-1 2.5-1-2.5L42.5 11l2.5-1z"
        fill="#16ad7a"
        opacity="0.7"
      />
      {/* Star bottom-right */}
      <path
        d="M50 44l1.2 2.8 2.8 1.2-2.8 1.2L50 52l-1.2-2.8L46 48l2.8-1.2z"
        fill="#16ad7a"
        opacity="0.5"
      />
      {/* R letterform */}
      <path
        d="M22 22h12c4.4 0 8 3.6 8 8s-3.6 8-8 8h-3l9 10h-7l-8.5-10H28v10h-6V22zm6 5.5v5h6c1.4 0 2.5-1.1 2.5-2.5s-1.1-2.5-2.5-2.5h-6z"
        fill="#fafafa"
      />
    </svg>
  );
}
