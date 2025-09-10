"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface ChatModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

export function ChatModal({ isOpen, onOpenChange }: ChatModalProps) {
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<Array<{ role: string; content: string }>>([]);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;

    const userMessage = { role: "user", content: chatMessage };
    setChatHistory((prev) => [...prev, userMessage]);
    setChatMessage("");

    setTimeout(() => {
      const botResponse = { role: "assistant", content: "This is a placeholder response. AI integration coming soon!" };
      setChatHistory((prev) => [...prev, botResponse]);
    }, 500);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="p-0 max-w-2xl h-[70vh] flex flex-col">
        <DialogHeader className="p-6 border-b">
          <DialogTitle>AI Assistant</DialogTitle>
        </DialogHeader>

        {/* Area Pesan Chat */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {chatHistory.length === 0 && (
            <div className="text-center text-gray-500 pt-16">
              Ask me anything about your hotel data. For example: "What was our total revenue last month?"
            </div>
          )}
          {chatHistory.map((message, index) => (
            <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.role === "user" ? "bg-primary text-primary-foreground" : "bg-gray-100 text-gray-900"
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
        </div>

        {/* Input Pesan Chat */}
        <div className="p-6 border-t bg-white">
          <form onSubmit={handleChatSubmit} className="flex gap-2">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Ask me anything..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
            <Button type="submit">Send</Button>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}
