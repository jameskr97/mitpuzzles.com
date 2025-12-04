import { cva, type VariantProps } from "class-variance-authority";

export { default as Badge } from "./Badge.vue";

export const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-md border px-2 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow] overflow-hidden",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground [a&]:hover:bg-primary/90",
        secondary: "border-transparent bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90",
        destructive:
          "border-transparent bg-destructive text-white [a&]:hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
        blue: "border-transparent bg-blue-500 text-white [a&]:hover:bg-blue-600 focus-visible:ring-blue-200 dark:focus-visible:ring-blue-400 dark:bg-blue-700",
        red: "border-transparent bg-red-500 text-white [a&]:hover:bg-red-600 focus-visible:ring-red-200 dark:focus-visible:ring-red-400 dark:bg-red-700",
        green: "border-transparent bg-green-500 text-white [a&]:hover:bg-green-600 focus-visible:ring-green-200 dark:focus-visible:ring-green-400 dark:bg-green-700",
        purple: "border-transparent bg-purple-500 text-white [a&]:hover:bg-purple-600 focus-visible:ring-purple-200 dark:focus-visible:ring-purple-400 dark:bg-purple-700",
        outline: "text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);
export type BadgeVariants = VariantProps<typeof badgeVariants>;
