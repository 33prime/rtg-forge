interface RtgMarkProps {
  className?: string;
  size?: number;
}

export default function RtgMark({ className, size = 32 }: RtgMarkProps) {
  return (
    <img
      src="/favicon.svg"
      alt="RTG"
      width={size}
      height={size}
      className={className}
    />
  );
}
