"use client";
import { Upload, Bot, BarChart3, Users } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onUploadClick?: () => void;
  page: "dashboard" | "users" | "chat";
}

export function Header({ onUploadClick, page }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto md:px-8">
        <div className="flex justify-between items-center h-16">
          <a href="/" className="text-2xl font-bold text-gray-900 no-underline">
            DashAgent
          </a>

          <div className="flex items-center gap-3">
            {page === "dashboard" && (
              <>
                <Button onClick={onUploadClick} variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
                  <Upload className="w-5 h-5" />
                  Upload Data
                </Button>
                <a href="/users">
                  <Button variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
                    <Users className="w-5 h-5" />
                    Manage Users
                  </Button>
                </a>
                <a href="/chat">
                  <Button variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
                    <Bot className="w-5 h-5" />
                    Chat with AI
                  </Button>
                </a>
              </>
            )}

            {page === "users" && (
              <a href="/">
                <Button variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
                  <BarChart3 className="w-5 h-5" />
                  Analytics Dashboard
                </Button>
              </a>
            )}

            {page === "chat" && (
              <a href="/">
                <Button variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
                  <BarChart3 className="w-5 h-5" />
                  Analytics Dashboard
                </Button>
              </a>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
