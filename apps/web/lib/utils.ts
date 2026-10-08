import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: unknown, digits = 2): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return value.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

export function glucoseColor(glucose: number): string {
  const t = Math.min(1, Math.max(0, (glucose - 80) / 120));
  const hue = 172 - t * 140;
  return `hsl(${hue} 62% 58%)`;
}
