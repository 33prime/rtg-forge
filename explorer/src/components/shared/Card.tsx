import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
  padding?: boolean;
}

export default function Card({ children, href, onClick, className, padding = true }: CardProps) {
  const navigate = useNavigate();

  const isClickable = !!href || !!onClick;

  const handleClick = () => {
    if (href) {
      navigate(href);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onClick={isClickable ? handleClick : undefined}
      onKeyDown={
        isClickable
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleClick();
              }
            }
          : undefined
      }
      className={clsx(
        'rounded-lg border border-border bg-surface transition-all',
        isClickable && 'cursor-pointer hover:border-[#3f3f46] hover:bg-surface-hover',
        padding && 'p-5',
        className
      )}
    >
      {children}
    </div>
  );
}
