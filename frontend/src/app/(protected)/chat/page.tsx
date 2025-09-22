"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Header } from "@/components/dashboard/Header";
import { Bot, User, Plus, MessageSquare, Menu } from "lucide-react";

// Tipe data untuk pesan dan percakapan
interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

// Data awal untuk contoh
const initialConversations: Conversation[] = [
  {
    id: "1",
    title: "Analisis Pendapatan Juli",
    messages: [
      { role: "assistant", content: "Hello! How can I help you analyze your hotel data today?" },
      { role: "user", content: "What was our total revenue in July?" },
      { role: "assistant", content: "The total revenue for July was Rp 1.2 Miliar." },
    ],
  },
  {
    id: "2",
    title: "Segmentasi Tamu Asing",
    messages: [{ role: "assistant", content: "Ready for a new analysis. What can I help with?" }],
  },
];

const ConversationSidebar = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
}: {
  conversations: Conversation[];
  activeConversationId: string;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}) => (
  <aside className="w-full h-full bg-white pt-12 md:p-4 flex flex-col space-y-4">
    <Button onClick={onNewChat} className="w-full">
      <Plus className="mr-2 h-4 w-4" />
      New Chat
    </Button>
    <div className="flex-1 overflow-y-auto">
      <p className="text-xs font-semibold text-gray-500 uppercase mb-2 px-3">Recent</p>
      <nav className="space-y-1">
        {conversations.map((conv) => (
          <button
            key={conv.id}
            onClick={() => onSelectConversation(conv.id)}
            className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-3 transition-colors ${
              activeConversationId === conv.id ? "bg-primary/10 text-primary font-semibold" : "hover:bg-gray-100"
            }`}
          >
            <MessageSquare size={16} className="flex-shrink-0" />
            <span className="truncate flex-1">{conv.title}</span>
          </button>
        ))}
      </nav>
    </div>
  </aside>
);

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>(initialConversations);
  const [activeConversationId, setActiveConversationId] = useState<string>("1");
  const [chatMessage, setChatMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const activeConversation = conversations.find((c) => c.id === activeConversationId);

  const handleNewChat = () => {
    const newId = `conv_${Date.now()}`;
    const newConversation: Conversation = {
      id: newId,
      title: "New Chat",
      messages: [{ role: "assistant", content: "Hello! How can I help you analyze your hotel data today?" }],
    };
    setConversations((prev) => [newConversation, ...prev]);
    setActiveConversationId(newId);
    setIsSidebarOpen(false);
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
    setIsSidebarOpen(false);
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim() || isLoading || !activeConversationId) return;

    const userMessage: Message = { role: "user", content: chatMessage };

    setConversations((prevConvos) =>
      prevConvos.map((convo) => (convo.id === activeConversationId ? { ...convo, messages: [...convo.messages, userMessage] } : convo))
    );

    setChatMessage("");
    setIsLoading(true);

    // TODO: Ganti dengan integrasi API Gemini Anda
    setTimeout(() => {
      const botResponse: Message = { role: "assistant", content: "This is a placeholder response. AI integration coming soon!" };

      // Tambahkan respons bot ke percakapan aktif
      setConversations((prevConvos) =>
        prevConvos.map((convo) => (convo.id === activeConversationId ? { ...convo, messages: [...convo.messages, botResponse] } : convo))
      );
      setIsLoading(false);
    }, 1500);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <Header page="chat" />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar untuk Desktop */}
        <div className="w-64 border-r hidden md:block">
          <ConversationSidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewChat={handleNewChat}
          />
        </div>

        {/* Area Chat Utama */}
        <main className="flex-1 flex flex-col">
          {/* Header Mobile */}
          <div className="md:hidden flex items-center justify-between p-4 border-b bg-white">
            <Sheet open={isSidebarOpen} onOpenChange={setIsSidebarOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                  <Menu className="h-6 w-6" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0 w-64">
                <ConversationSidebar
                  conversations={conversations}
                  activeConversationId={activeConversationId}
                  onSelectConversation={handleSelectConversation}
                  onNewChat={handleNewChat}
                />
              </SheetContent>
            </Sheet>
            <h2 className="text-lg font-semibold truncate">{activeConversation?.title}</h2>
            <div className="w-10"></div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
            {activeConversation?.messages.map((message, index) => (
              <div key={index} className={`flex items-start gap-4 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                {message.role === "assistant" && (
                  <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-700">
                    <Bot size={18} />
                  </span>
                )}
                <div
                  className={`px-4 py-3 rounded-lg max-w-lg ${message.role === "user" ? "bg-primary text-primary-foreground" : "bg-white shadow-sm"}`}
                >
                  <p className="text-sm">{message.content}</p>
                </div>
                {message.role === "user" && (
                  <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-primary text-primary-foreground">
                    <User size={18} />
                  </span>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex items-start gap-4">
                <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-700">
                  <Bot size={18} />
                </span>
                <div className="px-4 py-3 rounded-lg bg-white shadow-sm">
                  <p className="text-sm text-gray-500 italic">Thinking...</p>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 md:p-6 border-t bg-white">
            <form onSubmit={handleChatSubmit} className="flex gap-2 items-center max-w-4xl mx-auto">
              <input
                type="text"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="Ask about revenue, occupancy, guest segments..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                disabled={isLoading}
              />
              <Button type="submit" disabled={isLoading || !chatMessage.trim()}>
                {isLoading ? "Sending..." : "Send"}
              </Button>
            </form>
            <p className="text-xs text-gray-500 mt-2 text-center">DashAgent AI can make mistakes. Consider checking important information.</p>
          </div>
        </main>
      </div>
    </div>
  );
}
