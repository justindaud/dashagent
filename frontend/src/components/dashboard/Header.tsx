"use client";
import { Upload, Bot, BarChart3, Users, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import Link from "next/link";

interface HeaderProps {
  onUploadClick?: () => void;
  page: "dashboard" | "users" | "chat";
}

export function Header({ onUploadClick, page }: HeaderProps) {
  const renderNavLinks = (isMobile = false) => {
    if (page === "dashboard") {
      return (
        <>
          <Button onClick={onUploadClick} variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
            <Upload className="w-5 h-5" />
            <span className={isMobile ? "" : "hidden md:inline"}>Upload Data</span>
          </Button>
          <Link href="/users" passHref>
            <Button variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
              <Users className="w-5 h-5" />
              <span className={isMobile ? "" : "hidden md:inline"}>Manage Users</span>
            </Button>
          </Link>
          <Link href="/chat" passHref>
            <Button variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
              <Bot className="w-5 h-5" />
              <span className={isMobile ? "" : "hidden md:inline"}>Chat with AI</span>
            </Button>
          </Link>
        </>
      );
    }
    return (
      <Link href="/" passHref>
        <Button variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
          <BarChart3 className="w-5 h-5" />
          <span className={isMobile ? "" : "hidden md:inline"}>Analytics Dashboard</span>
        </Button>
      </Link>
    );
  };

  const renderMobileMenu = () => {
    const commonItemClass = "w-full justify-start gap-2";
    if (page === "dashboard") {
      return (
        <>
          <DropdownMenuItem onClick={onUploadClick} className={commonItemClass}>
            <Upload className="w-5 h-5" /> Upload Data
          </DropdownMenuItem>
          <Link href="/users" passHref>
            <DropdownMenuItem className={commonItemClass}>
              <Users className="w-5 h-5" /> Manage Users
            </DropdownMenuItem>
          </Link>
          <Link href="/chat" passHref>
            <DropdownMenuItem className={commonItemClass}>
              <Bot className="w-5 h-5" /> Chat with AI
            </DropdownMenuItem>
          </Link>
        </>
      );
    }
    return (
      <Link href="/" passHref>
        <DropdownMenuItem className={commonItemClass}>
          <BarChart3 className="w-5 h-5" /> Analytics Dashboard
        </DropdownMenuItem>
      </Link>
    );
  };

  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" passHref>
            <span className="text-2xl font-bold text-gray-900 no-underline cursor-pointer">DashAgent</span>
          </Link>

          <div className="hidden md:flex items-center gap-2 sm:gap-3">{renderNavLinks()}</div>

          <div className="md:hidden">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  <Menu className="h-6 w-6" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                {renderMobileMenu()}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  );
}
