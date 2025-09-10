"use client";
import { Upload, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onUploadClick: () => void;
  onChatClick: () => void;
}

export function Header({ onUploadClick, onChatClick }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto md:px-8">
        <div className="flex justify-between items-center h-16">
          <h1 className="text-2xl font-bold text-gray-900">DashAgent</h1>
          <div className="flex items-center gap-3">
            <Button onClick={onUploadClick} variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
              <Upload className="w-5 h-5" />
              Upload Data
            </Button>
            <Button onClick={onChatClick} variant="outline" className="flex items-center gap-2 border-primary text-primary hover:text-primary">
              <Bot className="w-5 h-5" />
              Chat with AI
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
