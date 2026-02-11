# Tailwind Design System

Patterns for building consistent, maintainable UIs with Tailwind CSS. Use design tokens, component variants, and the `cn()` utility to keep styling predictable and composable.

---

## The cn() Utility

Use `cn()` (powered by `clsx` + `tailwind-merge`) for all conditional and merged class names. Never do string concatenation for Tailwind classes.

```tsx
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### Why cn()

- `clsx` handles conditional classes: `clsx("base", isActive && "bg-blue-500")`
- `tailwind-merge` resolves conflicts: `twMerge("px-4 px-6")` becomes `"px-6"`
- Together they handle all class composition needs

---

## Component Variants with cva()

Use `class-variance-authority` (cva) for components with multiple variants:

```tsx
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
  // Base classes applied to ALL variants
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 py-2",
        lg: "h-12 px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  },
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
```

### Variant Rules

1. Base classes go in the first argument of `cva()`
2. Each variant dimension gets its own key in `variants`
3. Always provide `defaultVariants`
4. Expose `className` prop and merge with `cn()` for overrides
5. Export the variants function for use in composed components

---

## Design Token Consistency

Use Tailwind's spacing/color/typography scale consistently. Never use arbitrary values when a scale value exists.

### Spacing Scale

```
Use: p-1 p-2 p-3 p-4 p-6 p-8 p-12 p-16
Avoid: p-[7px] p-[13px] p-[22px]
```

Stick to the Tailwind spacing scale (multiples of 4px by default). Use arbitrary values only when matching exact design specs from Figma.

### Color Tokens

Define semantic colors in `tailwind.config.ts`:

```ts
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
      },
    },
  },
};
```

Then reference semantic tokens in components:

```tsx
// YES — semantic tokens
<div className="bg-background text-foreground border-border" />

// NO — hardcoded colors
<div className="bg-white text-gray-900 border-gray-200" />
```

---

## Responsive Design

Use Tailwind's mobile-first responsive prefixes. Design for mobile, then add breakpoints.

```tsx
// Mobile-first: stack on mobile, grid on larger screens
<div className="flex flex-col gap-4 sm:grid sm:grid-cols-2 lg:grid-cols-3">
  {items.map((item) => (
    <Card key={item.id} />
  ))}
</div>
```

### Breakpoint Reference

| Prefix | Min Width | Use For |
|---|---|---|
| (none) | 0px | Mobile base |
| `sm:` | 640px | Large phones, small tablets |
| `md:` | 768px | Tablets |
| `lg:` | 1024px | Small laptops |
| `xl:` | 1280px | Desktops |
| `2xl:` | 1536px | Large desktops |

### Responsive Rules

1. Start with mobile layout (no prefix)
2. Add `sm:` and up for progressive enhancement
3. Never hide critical content at any breakpoint
4. Test all breakpoints, not just mobile and desktop

---

## Dark Mode

Implement dark mode using CSS variables and Tailwind's `dark:` prefix.

```css
/* globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 47.4% 11.2%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
  }
}
```

```tsx
// Components automatically adapt via CSS variables
<div className="bg-background text-foreground">
  Adapts to light/dark automatically
</div>

// For cases where you need explicit dark overrides:
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  Explicit dark mode override
</div>
```

### Dark Mode Rules

1. Use CSS variables for all colors (auto-adapts to theme)
2. Use explicit `dark:` only when CSS variables are insufficient
3. Test both modes during development, not as an afterthought
4. Ensure sufficient contrast in both modes

---

## Layout Patterns

### Container

```tsx
<div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
  {/* Content constrained to max width with responsive padding */}
</div>
```

### Stack (Vertical Spacing)

```tsx
<div className="flex flex-col gap-4">
  <Component />
  <Component />
</div>
```

### Cluster (Horizontal Wrap)

```tsx
<div className="flex flex-wrap gap-2">
  <Tag />
  <Tag />
  <Tag />
</div>
```

### Sidebar Layout

```tsx
<div className="flex flex-col md:flex-row gap-6">
  <aside className="w-full md:w-64 shrink-0">Sidebar</aside>
  <main className="flex-1 min-w-0">Content</main>
</div>
```

---

## Anti-Patterns

```tsx
// BAD: Inline styles mixed with Tailwind
<div className="flex gap-4" style={{ padding: "20px", backgroundColor: "#f0f0f0" }}>

// BAD: String concatenation for classes
<div className={"px-4 " + (isActive ? "bg-blue-500" : "bg-gray-500")}>

// BAD: Arbitrary values when scale values exist
<div className="p-[16px] m-[24px] text-[14px]">
// Should be: p-4 m-6 text-sm

// BAD: Not using cn() for conditional classes
<div className={`px-4 ${isActive ? "bg-blue-500" : ""} ${isLarge ? "text-lg" : ""}`}>
// Should be: cn("px-4", isActive && "bg-blue-500", isLarge && "text-lg")
```
