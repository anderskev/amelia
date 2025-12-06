---
name: shadcn-ui
description: shadcn/ui component patterns with Radix primitives and Tailwind styling. Use when building UI components, using CVA variants, implementing compound components, or styling with data-slot attributes. Triggers on shadcn, cva, cn(), data-slot, Radix, Button, Card, Dialog, VariantProps.
---

# shadcn/ui Component Development

This skill covers component patterns, styling techniques, and architectural decisions used in shadcn/ui, a collection of re-usable components built with Radix UI primitives and styled with Tailwind CSS.

## Quick Reference

### The cn() Utility

Every shadcn/ui component uses the `cn()` utility for merging Tailwind classes:

```tsx
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

This utility combines `clsx` for conditional class application with `tailwind-merge` for intelligent Tailwind class conflict resolution.

### Basic CVA Pattern

Components use Class Variance Authority (CVA) for variant-based styling:

```tsx
import { cva, type VariantProps } from "class-variance-authority"

const componentVariants = cva(
  "base-classes-applied-to-all-variants",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        outline: "border bg-background",
      },
      size: {
        sm: "h-8 px-3",
        lg: "h-10 px-6",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "sm",
    },
  }
)

function Component({
  variant,
  size,
  className,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof componentVariants>) {
  return (
    <button
      className={cn(componentVariants({ variant, size }), className)}
      {...props}
    />
  )
}
```

## Component Anatomy

### Props Typing Pattern

Every component follows this TypeScript pattern:

```tsx
// For HTML elements
function Component({
  className,
  ...props
}: React.ComponentProps<"element">) {
  return <element className={cn("base-classes", className)} {...props} />
}

// For Radix primitives
function Component({
  className,
  ...props
}: React.ComponentProps<typeof RadixPrimitive.Root>) {
  return (
    <RadixPrimitive.Root
      className={cn("base-classes", className)}
      {...props}
    />
  )
}

// With CVA variants
function Component({
  variant,
  size,
  className,
  ...props
}: React.ComponentProps<"element"> & VariantProps<typeof variants>) {
  return (
    <element
      className={cn(variants({ variant, size }), className)}
      {...props}
    />
  )
}

// With asChild prop
function Component({
  asChild = false,
  className,
  ...props
}: React.ComponentProps<"element"> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "element"
  return <Comp className={cn("base-classes", className)} {...props} />
}
```

### The asChild Pattern

The `asChild` prop enables polymorphic rendering using `@radix-ui/react-slot`:

```tsx
import { Slot } from "@radix-ui/react-slot"

function Button({
  asChild = false,
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
}
```

**Usage:**
```tsx
// Renders as <button>
<Button>Click me</Button>

// Renders as <a> with button styling
<Button asChild>
  <a href="/home">Home</a>
</Button>

// Renders as Next.js Link
<Button asChild>
  <Link href="/dashboard">Dashboard</Link>
</Button>
```

The `Slot` component merges props and classes onto the child element.

### data-slot Attributes

Every component includes a `data-slot` attribute for CSS targeting:

```tsx
function Button({ ...props }) {
  return <button data-slot="button" {...props} />
}

function Card({ ...props }) {
  return <div data-slot="card" {...props} />
}

function CardHeader({ ...props }) {
  return <div data-slot="card-header" {...props} />
}
```

**CSS Targeting:**
```css
/* Target specific components */
[data-slot="button"] { /* styles */ }

/* Target within parent */
[data-slot="card"] [data-slot="button"] { /* styles */ }
```

**Tailwind Usage:**
```tsx
// Style all buttons within this div
<div className="[&_[data-slot=button]]:shadow-lg">
  <Button>Automatically styled</Button>
</div>
```

**Conditional Layouts:**
```tsx
function CardHeader({ className, ...props }) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "grid gap-2",
        // Two columns when CardAction is present
        "has-data-[slot=card-action]:grid-cols-[1fr_auto]",
        className
      )}
      {...props}
    />
  )
}
```

## Component Patterns

### Compound Components

Complex UI is split into multiple related components that compose together:

```tsx
// Export all parts
export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }

// Each part is independently typed
function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card"
      className={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        className
      )}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-header"
      className={cn("grid gap-2 px-6", className)}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-title"
      className={cn("leading-none font-semibold", className)}
      {...props}
    />
  )
}
```

**Usage:**
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

### Context for Complex Components

Components with shared state across multiple children use React Context:

```tsx
type ComponentContextValue = {
  state: string
  setState: (state: string) => void
}

const ComponentContext = React.createContext<ComponentContextValue | null>(null)

function useComponent() {
  const context = React.useContext(ComponentContext)
  if (!context) {
    throw new Error("useComponent must be used within ComponentProvider")
  }
  return context
}

function ComponentProvider({ children, defaultState }: Props) {
  const [state, setState] = React.useState(defaultState)

  const contextValue = React.useMemo(
    () => ({ state, setState }),
    [state, setState]
  )

  return (
    <ComponentContext.Provider value={contextValue}>
      {children}
    </ComponentContext.Provider>
  )
}

function ComponentChild() {
  const { state, setState } = useComponent()
  return <div>{state}</div>
}
```

**Best Practices:**
- Memoize context value to prevent unnecessary re-renders
- Provide custom hook with error checking
- Type context as `Type | null` to enforce provider usage
- Use `React.useCallback` for stable function references

### Controlled and Uncontrolled State

Support both patterns for flexibility:

```tsx
function Component({
  defaultValue,
  value: valueProp,
  onValueChange: setValueProp,
  ...props
}) {
  // Internal state
  const [_value, _setValue] = React.useState(defaultValue)

  // Use prop if provided, otherwise internal state
  const value = valueProp ?? _value

  const setValue = React.useCallback(
    (newValue) => {
      if (setValueProp) {
        setValueProp(newValue)
      } else {
        _setValue(newValue)
      }
    },
    [setValueProp]
  )

  return <input value={value} onChange={(e) => setValue(e.target.value)} />
}
```

**Uncontrolled usage:**
```tsx
<Component defaultValue="initial" />
```

**Controlled usage:**
```tsx
const [value, setValue] = useState("initial")
<Component value={value} onValueChange={setValue} />
```

### Wrapping Radix Primitives

Many components wrap Radix UI primitives:

```tsx
"use client"

import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"
import { cn } from "@/lib/utils"

function Label({
  className,
  ...props
}: React.ComponentProps<typeof LabelPrimitive.Root>) {
  return (
    <LabelPrimitive.Root
      data-slot="label"
      className={cn(
        "flex items-center gap-2 text-sm font-medium",
        className
      )}
      {...props}
    />
  )
}

export { Label }
```

**Key Points:**
- Add `"use client"` directive for client components
- Type props as `React.ComponentProps<typeof Primitive.Root>`
- Add `data-slot` attribute for CSS targeting
- Merge primitive props with spread operator

## Styling Techniques

### CVA Variant Patterns

#### Multiple Variant Dimensions

```tsx
const buttonVariants = cva("base-classes", {
  variants: {
    variant: {
      default: "bg-primary text-primary-foreground",
      destructive: "bg-destructive text-white",
      outline: "border bg-background",
      ghost: "hover:bg-accent",
      link: "text-primary underline-offset-4 hover:underline",
    },
    size: {
      default: "h-9 px-4 py-2",
      sm: "h-8 px-3",
      lg: "h-10 px-6",
      icon: "size-9",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
})
```

#### Compound Variants

Apply classes when multiple conditions are met:

```tsx
const variants = cva("base", {
  variants: {
    variant: { default: "bg-primary", outline: "border" },
    size: { sm: "h-8", lg: "h-12" },
  },
  compoundVariants: [
    {
      variant: "outline",
      size: "lg",
      class: "border-2", // Thicker border for large outlined buttons
    },
  ],
})
```

#### Type Extraction

```tsx
import { type VariantProps } from "class-variance-authority"

const componentVariants = cva(/* ... */)

// Extract variant prop types
type ComponentVariants = VariantProps<typeof componentVariants>
// Result: { variant?: "default" | "outline", size?: "sm" | "lg" }

// Use in component props
interface ComponentProps
  extends React.ComponentProps<"button">,
    VariantProps<typeof componentVariants> {
  asChild?: boolean
}
```

#### Export Pattern

Always export both component and variants for reusability:

```tsx
const buttonVariants = cva(/* ... */)

function Button({ ... }) {
  return <button className={cn(buttonVariants({ variant, size }))} />
}

export { Button, buttonVariants }
```

This allows external composition:

```tsx
import { buttonVariants } from "@/components/ui/button"

function CustomLink() {
  return (
    <a className={cn(buttonVariants({ variant: "outline" }), "custom-class")}>
      Link styled as button
    </a>
  )
}
```

### Modern CSS Selectors

#### has() Selector

Adjust parent styling based on children:

```tsx
// Button adjusts padding when it contains an icon
<button className="px-4 has-[>svg]:px-3">
  <Icon />
  Text
</button>

// CVA integration
const buttonVariants = cva("...", {
  variants: {
    size: {
      default: "h-9 px-4 has-[>svg]:px-3",
      sm: "h-8 px-3 has-[>svg]:px-2.5",
    },
  },
})

// Conditional grid layout
<div className="grid grid-rows-[auto_auto] has-data-[slot=action]:grid-cols-[1fr_auto]">
  <div>Title</div>
  <div>Description</div>
  <div data-slot="action">Action</div> {/* Triggers two-column layout */}
</div>
```

#### Group and Peer Selectors

Named groups and peers for complex interactions:

```tsx
// Parent controls child visibility
<div className="group" data-state="collapsed">
  <div className="group-data-[state=collapsed]:hidden">
    Hidden when collapsed
  </div>
</div>

// Sibling interactions
<button className="peer/menu-button" data-active="true">
  Menu
</button>
<div className="peer-data-[active=true]/menu-button:text-accent">
  Highlighted when sibling is active
</div>
```

#### Parent Class Selectors

Style based on parent classes:

```tsx
<div className="border-t">
  <div className="[.border-t]:pt-6">
    Adds top padding when parent has border-t
  </div>
</div>
```

#### Container Queries

Responsive styling based on container size:

```tsx
<div className="@container/card">
  <div className="gap-2 @container/card:gap-4 @md:flex-row">
    Adjusts based on container width
  </div>
</div>
```

### Focus and Accessibility States

#### Focus Visible

```tsx
className={cn(
  "outline-none",
  "focus-visible:border-ring",
  "focus-visible:ring-ring/50",
  "focus-visible:ring-[3px]",
)}
```

#### ARIA Invalid

```tsx
className={cn(
  "aria-invalid:border-destructive",
  "aria-invalid:ring-destructive/20",
  "dark:aria-invalid:ring-destructive/40",
)}
```

#### Disabled States

```tsx
className={cn(
  "disabled:pointer-events-none",
  "disabled:cursor-not-allowed",
  "disabled:opacity-50",
  "peer-disabled:cursor-not-allowed",
  "peer-disabled:opacity-50",
)}
```

#### Screen Reader Only

```tsx
<span className="sr-only">Close</span>
```

### Dark Mode

Use Tailwind's dark mode with class strategy:

```tsx
className={cn(
  "bg-background text-foreground",
  "dark:bg-input/30",
  "dark:border-input",
  "dark:hover:bg-input/50",
)}
```

Semantic color tokens adapt automatically:
- `bg-background` / `text-foreground`
- `bg-primary` / `text-primary-foreground`
- `bg-card` / `text-card-foreground`
- `border-input`
- `text-muted-foreground`

## Decision Tables

### When to Use CVA

| Scenario | Use CVA | Alternative |
|----------|---------|-------------|
| Multiple visual variants (primary, outline, ghost) | Yes | Plain className |
| Size variations (sm, md, lg) | Yes | Plain className |
| Compound conditions (outline + large = thick border) | Yes | Conditional cn() |
| One-off custom styling | No | className prop |
| Dynamic colors from props | No | Inline styles or CSS variables |

### When to Use Compound Components

| Scenario | Use Compound | Alternative |
|----------|--------------|-------------|
| Complex UI with multiple semantic parts | Yes | Single component with many props |
| Optional sections (header, footer) | Yes | Boolean show/hide props |
| Different styling for each part | Yes | CSS selectors |
| Shared state between parts | Yes + Context | Props drilling |
| Simple wrapper with children | No | Single component |

### When to Use asChild

| Scenario | Use asChild | Alternative |
|----------|-------------|-------------|
| Component should work as link or button | Yes | Duplicate component |
| Need button styles on custom element | Yes | Export variant styles |
| Integration with routing libraries | Yes | Wrapper components |
| Always renders same element | No | Standard component |

### When to Use Context

| Scenario | Use Context | Alternative |
|----------|-------------|-------------|
| Deep prop drilling (>3 levels) | Yes | Props |
| State shared by many siblings | Yes | Lift state up |
| Plugin/extension architecture | Yes | Props |
| Simple parent-child communication | No | Props |
| Independent components | No | Props |

## Common Patterns

### Form Element Pattern

```tsx
function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        // Base styles
        "h-9 w-full rounded-md border px-3 py-1",
        // Focus state
        "outline-none",
        "focus-visible:border-ring",
        "focus-visible:ring-ring/50",
        "focus-visible:ring-[3px]",
        // Invalid state
        "aria-invalid:border-destructive",
        "aria-invalid:ring-destructive/20",
        // Disabled state
        "disabled:cursor-not-allowed",
        "disabled:opacity-50",
        // Pseudo-elements
        "placeholder:text-muted-foreground",
        // Dark mode
        "dark:bg-input/30",
        className
      )}
      {...props}
    />
  )
}
```

### Modal Pattern (Dialog)

```tsx
function DialogContent({ children, showCloseButton = true, ...props }) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Content
        data-slot="dialog-content"
        className={cn(
          // Layout
          "fixed top-[50%] left-[50%]",
          "translate-x-[-50%] translate-y-[-50%]",
          "w-full max-w-lg",
          // Styling
          "bg-background border rounded-lg p-6 shadow-lg",
          // Animations
          "data-[state=open]:animate-in",
          "data-[state=open]:fade-in-0",
          "data-[state=open]:zoom-in-95",
          "data-[state=closed]:animate-out",
          "data-[state=closed]:fade-out-0",
          "data-[state=closed]:zoom-out-95",
        )}
        {...props}
      >
        {children}
        {showCloseButton && (
          <DialogPrimitive.Close className="absolute top-4 right-4">
            <XIcon />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        )}
      </DialogPrimitive.Content>
    </DialogPortal>
  )
}
```

### Complex State Management (Sidebar)

```tsx
function SidebarProvider({ defaultOpen = true, children }) {
  const isMobile = useIsMobile()
  const [open, setOpen] = React.useState(defaultOpen)

  // Keyboard shortcut
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "b" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        setOpen((open) => !open)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const contextValue = React.useMemo(
    () => ({
      state: open ? "expanded" : "collapsed",
      open,
      setOpen,
      isMobile,
    }),
    [open, setOpen, isMobile]
  )

  return (
    <SidebarContext.Provider value={contextValue}>
      <div
        data-slot="sidebar-wrapper"
        style={{
          "--sidebar-width": "16rem",
          "--sidebar-width-icon": "3rem",
        } as React.CSSProperties}
      >
        {children}
      </div>
    </SidebarContext.Provider>
  )
}
```

## Reference Files

For comprehensive examples and advanced patterns, see:

- **[components.md](./references/components.md)** - Full component implementations (Button, Card, Badge, Input, Label, Textarea, Dialog)
- **[cva.md](./references/cva.md)** - CVA patterns including compound variants, responsive variants, type extraction
- **[patterns.md](./references/patterns.md)** - Architectural patterns including compound components, asChild polymorphism, controlled state, Context usage, data-slot targeting, has() selectors
