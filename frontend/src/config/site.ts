const DEFAULT_API_URL = "http://localhost:8000"

export const siteConfig = {
  name: "CGC Knowledge AI",
  shortName: "Knowledge AI",
  tagline: "Your company knowledge, instantly accessible.",
  description:
    "An enterprise AI knowledge assistant for grounded answers across company documentation.",
  url: process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
  apiUrl:
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ??
    DEFAULT_API_URL,
  locale: "en_US",
  themeColor: {
    light: "#ffffff",
    dark: "#0f1020",
  },
} as const

export type SiteConfig = typeof siteConfig
