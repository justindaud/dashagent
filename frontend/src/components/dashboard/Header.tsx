"use client";
import { useState } from "react";
import Link from "next/link";
import api from "@/lib/axios";
import { Upload, Bot, BarChart3, Users, Menu, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

interface HeaderProps {
  onUploadClick?: () => void;
  page: "dashboard" | "users" | "chat";
}

export function Header({ onUploadClick, page }: HeaderProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await api.post("/api/auth/logout");
    } catch (error) {
      console.error("Logout request failed, but proceeding with client-side cleanup:", error);
    } finally {
      localStorage.removeItem("isLoggedIn");
      window.location.href = "/auth";
    }
  };

  const navLinks = [
    { href: "/", icon: BarChart3, label: "Analytics Dashboard", page: ["users", "chat"] },
    { href: "/users", icon: Users, label: "Manage Users", page: ["dashboard"] },
    { href: "/chat", icon: Bot, label: "Chat with AI", page: ["dashboard"] },
  ];

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="text-2xl font-bold text-gray-900 no-underline">
            DashAgent
          </Link>

          {/* Navigasi Desktop */}
          <div className="hidden md:flex items-center gap-2">
            {page === "dashboard" && (
              <Button onClick={onUploadClick} variant="outline" className="flex items-center gap-2 text-primary hover:text-primary/80">
                <Upload className="w-4 h-4" />
                <span>Upload Data</span>
              </Button>
            )}
            {navLinks
              .filter((link) => link.page.includes(page))
              .map((link) => (
                <Link key={link.href} href={link.href} passHref>
                  <Button variant="outline" className="flex items-center gap-2 text-primary hover:text-primary/80">
                    <link.icon className="w-4 h-4" />
                    <span>{link.label}</span>
                  </Button>
                </Link>
              ))}
            <Button onClick={handleLogout} variant="destructive" className="flex items-center gap-2 ml-2">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>

          {/* Menu Hamburger Seluler */}
          <div className="md:hidden">
            <DropdownMenu open={isMenuOpen} onOpenChange={setIsMenuOpen}>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  <Menu className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {page === "dashboard" && (
                  <DropdownMenuItem onClick={onUploadClick}>
                    <Upload className="mr-2 h-4 w-4" />
                    <span>Upload Data</span>
                  </DropdownMenuItem>
                )}
                {navLinks
                  .filter((link) => link.page.includes(page))
                  .map((link) => (
                    <Link key={link.href} href={link.href} passHref>
                      <DropdownMenuItem>
                        <link.icon className="mr-2 h-4 w-4" />
                        <span>{link.label}</span>
                      </DropdownMenuItem>
                    </Link>
                  ))}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-500 focus:text-red-500">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Logout</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  );
}
