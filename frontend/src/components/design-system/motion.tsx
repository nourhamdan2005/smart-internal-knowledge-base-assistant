"use client"

import { motion, type HTMLMotionProps } from "motion/react"
import { useAppReducedMotion } from "@/features/preferences"

export const MOTION = {
  fast: 0.16,
  standard: 0.22,
  easing: [0.22, 1, 0.36, 1],
} as const

const transition = { duration: MOTION.standard, ease: MOTION.easing } as const

function useEntrance() {
  const reducedMotion = useAppReducedMotion()
  return reducedMotion
    ? { initial: false as const, animate: undefined }
    : {
        initial: { opacity: 0, y: 14 },
        animate: { opacity: 1, y: 0 },
      }
}

export function PageEntrance({ children, ...props }: Readonly<HTMLMotionProps<"div">>) {
  const entrance = useEntrance()
  return <motion.div {...entrance} transition={transition} {...props}>{children}</motion.div>
}

export function CardEntrance({
  children,
  delay = 0,
  ...props
}: Readonly<HTMLMotionProps<"div"> & { delay?: number }>) {
  const entrance = useEntrance()
  return <motion.div {...entrance} transition={{ ...transition, delay }} {...props}>{children}</motion.div>
}

export function FadeSlide({ children, ...props }: Readonly<HTMLMotionProps<"div">>) {
  const entrance = useEntrance()
  return <motion.div {...entrance} transition={transition} {...props}>{children}</motion.div>
}

export function HoverLift({ children, ...props }: Readonly<HTMLMotionProps<"div">>) {
  const reducedMotion = useAppReducedMotion()
  return (
    <motion.div
      whileHover={reducedMotion ? undefined : { y: -4 }}
      transition={{ duration: MOTION.fast }}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function StaggeredList({ children, ...props }: Readonly<HTMLMotionProps<"div">>) {
  const reducedMotion = useAppReducedMotion()
  return (
    <motion.div
      initial={reducedMotion ? false : "hidden"}
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: reducedMotion
            ? undefined
            : { staggerChildren: 0.04, delayChildren: 0.02 },
        },
      }}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function StaggeredItem({ children, ...props }: Readonly<HTMLMotionProps<"div">>) {
  const reducedMotion = useAppReducedMotion()
  return (
    <motion.div
      variants={{
        hidden: reducedMotion ? {} : { opacity: 0, y: 10 },
        visible: reducedMotion ? {} : { opacity: 1, y: 0 },
      }}
      transition={transition}
      {...props}
    >
      {children}
    </motion.div>
  )
}
