"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/dashboard/Header"; // Path corrected to use alias
import { Bot, User, Plus, MessageSquare } from "lucide-react";

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

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>(initialConversations);
  const [activeConversationId, setActiveConversationId] = useState<string>("1");
  const [chatMessage, setChatMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Cari percakapan yang sedang aktif
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
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim() || isLoading || !activeConversationId) return;

    const userMessage: Message = { role: "user", content: chatMessage };

    // Tambahkan pesan pengguna ke percakapan aktif
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
        {/* Sidebar untuk Daftar Percakapan */}
        <aside className="w-64 bg-white border-r p-4 flex-col space-y-4 hidden md:flex">
          <Button onClick={handleNewChat} className="w-full">
            <Plus className="mr-2 h-4 w-4" />
            New Chat
          </Button>
          <div className="flex-1 overflow-y-auto">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2 px-3">Recent</p>
            <nav className="space-y-1">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setActiveConversationId(conv.id)}
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

        {/* Area Chat Utama */}
        <main className="flex-1 flex flex-col">
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
