"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from "lucide-react"
import { DateRange } from "react-day-picker"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface DateRangePickerProps {
  dateRange: DateRange | undefined
  onDateRangeChange: (dateRange: DateRange | undefined) => void
  className?: string
  placeholder?: string
}

export function DateRangePicker({ dateRange, onDateRangeChange, className, placeholder = "Pick a date range" }: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)
  const [currentMonth, setCurrentMonth] = React.useState<Date>(dateRange?.from || new Date())
  
  const currentYear = currentMonth.getFullYear()
  const currentMonthIndex = currentMonth.getMonth()
  
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ]
  
  const years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - 5 + i)
  
  const handleMonthChange = (monthIndex: string) => {
    const newDate = new Date(currentYear, parseInt(monthIndex), 1)
    setCurrentMonth(newDate)
  }
  
  const handleYearChange = (year: string) => {
    const newDate = new Date(parseInt(year), currentMonthIndex, 1)
    setCurrentMonth(newDate)
  }
  
  const goToPreviousMonth = () => {
    const newDate = new Date(currentYear, currentMonthIndex - 1, 1)
    setCurrentMonth(newDate)
  }
  
  const goToNextMonth = () => {
    const newDate = new Date(currentYear, currentMonthIndex + 1, 1)
    setCurrentMonth(newDate)
  }

  return (
    <div className={cn("grid gap-2", className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button id="date" variant={"outline"} className={cn("w-full justify-start text-left font-normal", !dateRange && "text-muted-foreground")}>
            <CalendarIcon className="h-4 w-4" />
            {dateRange?.from ? (
              dateRange.to ? (<>{format(dateRange.from, "LLL dd, y")} -{" "}{format(dateRange.to, "LLL dd, y")}</>) : (format(dateRange.from, "LLL dd, y"))
            ) : (<span>{placeholder}</span>)}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <div className="p-3">
            <div className="flex items-center justify-between mb-2">
              <Button variant="ghost" size="sm" onClick={goToPreviousMonth}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <div className="flex items-center gap-2">
                <Select value={currentMonthIndex.toString()} onValueChange={handleMonthChange}>
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {months.map((month, index) => (
                      <SelectItem key={index} value={index.toString()}>
                        {month}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={currentYear.toString()} onValueChange={handleYearChange}>
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((year) => (
                      <SelectItem key={year} value={year.toString()}>
                        {year}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button variant="ghost" size="sm" onClick={goToNextMonth}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
                  <Calendar
                    initialFocus
                    mode="range"
                    defaultMonth={currentMonth}
                    selected={dateRange}
                    onSelect={(range) => { 
                      // Handle single day selection
                      if (range?.from && !range.to) {
                        // If only start date is selected, set end date to same date
                        const singleDayRange = {
                          from: range.from,
                          to: range.from
                        };
                        onDateRangeChange(singleDayRange);
                      } else {
                        onDateRangeChange(range);
                      }
                    }}
                    numberOfMonths={1}
                    month={currentMonth}
                    onMonthChange={setCurrentMonth}
                  />
                  
                  {/* Done Button */}
          <div className="p-3 border-t">
            <Button 
              onClick={() => setOpen(false)} 
              className="w-full"
              disabled={!dateRange?.from}
            >
              Done
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
