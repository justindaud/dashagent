import React from "react"
import { cn } from "@/lib/utils"

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

interface DialogContentProps {
  className?: string
  children: React.ReactNode
}

interface DialogHeaderProps {
  className?: string
  children: React.ReactNode
}

interface DialogTitleProps {
  className?: string
  children: React.ReactNode
}

export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {children}
    </div>
  )
}

export const DialogContent: React.FC<DialogContentProps> = ({ className, children }) => (
  <div className={cn(
    "relative z-50 w-full max-w-4xl h-[80vh] bg-white rounded-lg shadow-lg border",
    className
  )}>
    {children}
  </div>
)

export const DialogHeader: React.FC<DialogHeaderProps> = ({ className, children }) => (
  <div className={cn(
    "flex items-center justify-between p-6 border-b",
    className
  )}>
    {children}
  </div>
)

export const DialogTitle: React.FC<DialogTitleProps> = ({ className, children }) => (
  <h2 className={cn("text-xl font-semibold text-gray-900", className)}>
    {children}
  </h2>
)
