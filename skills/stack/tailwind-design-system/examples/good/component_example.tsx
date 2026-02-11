/**
 * Good Tailwind component example.
 *
 * Demonstrates:
 * - cn() for class merging
 * - cva() for component variants
 * - Semantic color tokens
 * - Consistent spacing scale
 * - Responsive design (mobile-first)
 * - Dark mode support
 * - Proper component composition
 */

import { cva, type VariantProps } from "class-variance-authority";
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// ---------------------------------------------------------------------------
// cn() utility
// ---------------------------------------------------------------------------

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ---------------------------------------------------------------------------
// Badge component with cva() variants
// ---------------------------------------------------------------------------

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary/10 text-primary",
        success: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
        warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
        danger: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
        neutral: "bg-muted text-muted-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

// ---------------------------------------------------------------------------
// Card component with consistent spacing and dark mode
// ---------------------------------------------------------------------------

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-background p-6 shadow-sm transition-shadow hover:shadow-md",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

function CardHeader({ className, children, ...props }: CardProps) {
  return (
    <div className={cn("flex items-center justify-between", className)} {...props}>
      {children}
    </div>
  );
}

function CardBody({ className, children, ...props }: CardProps) {
  return (
    <div className={cn("mt-4", className)} {...props}>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// InvoiceCard — composed from primitives
// ---------------------------------------------------------------------------

interface Invoice {
  id: string;
  customerName: string;
  status: "draft" | "sent" | "paid" | "overdue";
  total: number;
  lineItemCount: number;
}

const STATUS_VARIANT: Record<Invoice["status"], VariantProps<typeof badgeVariants>["variant"]> = {
  draft: "neutral",
  sent: "default",
  paid: "success",
  overdue: "danger",
};

interface InvoiceCardProps {
  invoice: Invoice;
  onSelect: (id: string) => void;
  isSelected?: boolean;
}

function InvoiceCard({ invoice, onSelect, isSelected = false }: InvoiceCardProps) {
  const formattedTotal = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(invoice.total);

  return (
    <Card
      className={cn(
        "cursor-pointer",
        isSelected && "ring-2 ring-primary ring-offset-2 ring-offset-background",
      )}
      onClick={() => onSelect(invoice.id)}
    >
      <CardHeader>
        <h3 className="text-sm font-medium text-foreground">{invoice.customerName}</h3>
        <Badge variant={STATUS_VARIANT[invoice.status]}>{invoice.status}</Badge>
      </CardHeader>
      <CardBody>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-semibold text-foreground">{formattedTotal}</span>
          <span className="text-sm text-muted-foreground">
            {invoice.lineItemCount} {invoice.lineItemCount === 1 ? "item" : "items"}
          </span>
        </div>
      </CardBody>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Invoice grid — responsive layout
// ---------------------------------------------------------------------------

interface InvoiceGridProps {
  invoices: Invoice[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function InvoiceGrid({ invoices, selectedId, onSelect }: InvoiceGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {invoices.map((invoice) => (
        <InvoiceCard
          key={invoice.id}
          invoice={invoice}
          onSelect={onSelect}
          isSelected={invoice.id === selectedId}
        />
      ))}
    </div>
  );
}
