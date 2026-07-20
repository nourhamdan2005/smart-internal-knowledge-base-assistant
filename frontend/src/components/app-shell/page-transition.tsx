"use client"

import { motion } from "motion/react"
import { usePathname } from "next/navigation"
import { useAppReducedMotion } from "@/features/preferences"

export function PageTransition({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname()
  const reducedMotion = useAppReducedMotion()

  return (
    <motion.div
      key={pathname}
      initial={reducedMotion ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reducedMotion ? 0 : 0.2, ease: "easeOut" }}
      className="min-h-full"
    >
      {children}
    </motion.div>
  )
}
