"use client";

import { useState, useEffect, useRef } from "react";
import api from "@/lib/axios";
import { Header } from "@/components/dashboard/Header";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Menu, Loader2 } from "lucide-react";
import { DesktopChatSidebar } from "@/components/chat/DesktopChatSidebar";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  session_id: string;
  title: string;
  messages: Message[];
  isLoadingMessages?: boolean;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [chatMessage, setChatMessage] = useState("");
  const [isLoadingReply, setIsLoadingReply] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [isDesktopSidebarCollapsed, setIsDesktopSidebarCollapsed] = useState(true);

  const [timer, setTimer] = useState(0);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoadingReply) {
      setTimer(0);
      interval = setInterval(() => {
        setTimer((prevTimer) => prevTimer + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isLoadingReply]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversations, activeConversationId, isLoadingReply]);

  const fetchConversations = async () => {
    setIsLoadingConversations(true);
    try {
      const response = await api.get("/sessions/");
      const fetchedSessions = (response.data.data || []).map((s: any) => ({
        ...s,
        messages: [],
      }));
      setConversations(fetchedSessions);
      if (fetchedSessions.length > 0 && !activeConversationId) {
        const firstSessionId = fetchedSessions[0].session_id;
        setActiveConversationId(firstSessionId);
        fetchMessagesForSession(firstSessionId);
      }
    } catch (error) {
      console.error("Failed to fetch conversations", error);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  const activeConversation = conversations.find((c) => c.session_id === activeConversationId);

  const handleNewChat = async () => {
    try {
      const response = await api.post("/sessions/", {});
      const newSessionData = response.data.data[0];
      const newConversation: Conversation = {
        session_id: newSessionData.session_id,
        title: newSessionData.title_suggestion,
        messages: [
          {
            role: "assistant",
            content: "Hello! How can I help you analyze your hotel data today?",
          },
        ],
      };
      setConversations((prev) => [newConversation, ...prev]);
      setActiveConversationId(newConversation.session_id);
      setIsMobileSidebarOpen(false);
      setIsDesktopSidebarCollapsed(true);
    } catch (error) {
      console.error("Failed to create new chat", error);
    }
  };

  const fetchMessagesForSession = async (sessionId: string) => {
    setConversations((prev) => prev.map((c) => (c.session_id === sessionId ? { ...c, isLoadingMessages: true } : c)));
    try {
      const response = await api.get(`/sessions/${sessionId}/messages/`);
      const sessionData = response.data.data[0];
      let newMessages: Message[] = [];
      if (sessionData && sessionData.runs) {
        sessionData.runs.forEach((run: any) => {
          run.messages.forEach((msg: any) => {
            if (msg.kind === "user_prompt") {
              const content = msg.content.split("USER PROMPT:")[1]?.split("\n\n")[0]?.trim() || msg.content;
              newMessages.push({ role: "user", content });
            } else if (msg.kind === "assistant_output") {
              newMessages.push({ role: "assistant", content: msg.content });
            }
          });
        });
      }
      setConversations((prev) => prev.map((c) => (c.session_id === sessionId ? { ...c, messages: newMessages, isLoadingMessages: false } : c)));
    } catch (error) {
      console.error("Failed to fetch messages for session", sessionId, error);
      setConversations((prev) => prev.map((c) => (c.session_id === sessionId ? { ...c, isLoadingMessages: false } : c)));
    }
  };

  const handleSelectConversation = (id: string) => {
    if (editingConversationId) return;
    setActiveConversationId(id);
    const targetConvo = conversations.find((c) => c.session_id === id);
    if (targetConvo && targetConvo.messages.length === 0) {
      fetchMessagesForSession(id);
    }
    setIsMobileSidebarOpen(false);
    setIsDesktopSidebarCollapsed(true);
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim() || isLoadingReply || !activeConversationId) return;
    const userMessage: Message = { role: "user", content: chatMessage };
    setConversations((prev) =>
      prev.map((convo) => (convo.session_id === activeConversationId ? { ...convo, messages: [...convo.messages, userMessage] } : convo))
    );
    const messageToSend = chatMessage;
    setChatMessage("");
    setIsLoadingReply(true);
    try {
      await api.post(`/sessions/${activeConversationId}/run/`, {
        user_input: messageToSend,
      });
      await fetchMessagesForSession(activeConversationId);
    } catch (error) {
      console.error("Error sending chat message:", error);
      setConversations((prev) =>
        prev.map((convo) => {
          if (convo.session_id === activeConversationId) {
            return {
              ...convo,
              messages: [...convo.messages, { role: "assistant", content: "Sorry, an error occurred." }],
            };
          }
          return convo;
        })
      );
    } finally {
      setIsLoadingReply(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      formRef.current?.requestSubmit();
    }
  };

  const handleStartEdit = (id: string, currentTitle: string) => {
    setEditingConversationId(id);
    setEditingTitle(currentTitle);
    setIsDesktopSidebarCollapsed(false);
  };

  const handleUpdateTitle = async () => {
    if (!editingConversationId || !editingTitle.trim()) {
      setEditingConversationId(null);
      return;
    }
    try {
      await api.put(`/sessions/${editingConversationId}/`, {
        title: editingTitle,
      });
      setConversations((prev) => prev.map((c) => (c.session_id === editingConversationId ? { ...c, title: editingTitle } : c)));
    } catch (error) {
      console.error("Failed to update title", error);
    } finally {
      setEditingConversationId(null);
      setEditingTitle("");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      <div className="hidden md:block">
        <Header page="chat" />
      </div>
      <div className="flex flex-1 overflow-hidden">
        {/* === Desktop Sidebar === */}
        <div
          className={`hidden md:flex flex-col bg-white border-r transition-all duration-300 ease-in-out ${
            isDesktopSidebarCollapsed ? "w-20" : "w-72"
          }`}
          onMouseEnter={() => !editingConversationId && setIsDesktopSidebarCollapsed(false)}
          onMouseLeave={() => !editingConversationId && setIsDesktopSidebarCollapsed(true)}
        >
          <DesktopChatSidebar
            isCollapsed={isDesktopSidebarCollapsed}
            onNewChat={handleNewChat}
            isLoadingConversations={isLoadingConversations}
            conversations={conversations}
            activeConversationId={activeConversationId}
            editingConversationId={editingConversationId}
            editingTitle={editingTitle}
            setEditingTitle={setEditingTitle}
            onSaveEdit={handleUpdateTitle}
            onStartEdit={handleStartEdit}
            onSelect={handleSelectConversation}
          />
        </div>

        <main className="flex-1 flex flex-col ">
          <div className="flex-1 overflow-y-auto px-4 pb-4 md:p-6 space-y-6 max-w-4xl w-full mx-auto hide-scrollbar">
            {/* === Mobile Header & Sidebar === */}
            <div className="md:hidden flex items-center gap-2 py-2 border-b sticky top-0 bg-white z-10">
              <Sheet open={isMobileSidebarOpen} onOpenChange={setIsMobileSidebarOpen}>
                <SheetTrigger asChild>
                  <Button variant="outline" size="icon">
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="p-0 w-72">
                  <aside className="w-full bg-white p-4 flex flex-col space-y-4 h-full">
                    <Button onClick={handleNewChat} className="w-full">
                      <Plus className="mr-2 h-4 w-4" /> New Chat
                    </Button>
                    <div className="flex-1 overflow-y-auto">
                      <p className="text-xs font-semibold text-gray-500 uppercase mb-2 px-3">Recent</p>
                      <nav className="space-y-1">
                        {isLoadingConversations ? (
                          <div className="space-y-2 px-2">
                            <Skeleton className="h-8 w-full" />
                            <Skeleton className="h-8 w-full" />
                          </div>
                        ) : (
                          conversations.map((conv) => (
                            <button
                              key={conv.session_id}
                              onClick={() => handleSelectConversation(conv.session_id)}
                              className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-3 transition-colors ${
                                activeConversationId === conv.session_id ? "bg-primary/10 text-primary font-semibold" : "hover:bg-gray-100"
                              }`}
                            >
                              <span className="truncate flex-1">{conv.title}</span>
                            </button>
                          ))
                        )}
                      </nav>
                    </div>
                  </aside>
                </SheetContent>
              </Sheet>
              <h2 className="text-lg font-semibold truncate pr-4">{activeConversation?.title || "Chat"}</h2>
            </div>

            {/* === Message List === */}
            {activeConversation?.isLoadingMessages ? (
              <div className="flex justify-center items-center h-full">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              activeConversation?.messages.map((message, index) => <ChatMessage key={index} message={message} />)
            )}

            {/* === Loading Reply Indicator === */}
            {isLoadingReply && (
              <div className="flex flex-col items-start gap-2">
                <div className="flex items-start">
                  <div className="px-4 py-3 rounded-lg flex items-center">
                    <span className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s] mx-1"></span>
                    <span className="h-2 w-2 bg-primary rounded-full animate-bounce"></span>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500 italic">AI has been thinking for {timer}s</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* === Chat Input Form === */}
          <ChatInput
            formRef={formRef}
            chatMessage={chatMessage}
            setChatMessage={setChatMessage}
            handleChatSubmit={handleChatSubmit}
            handleKeyDown={handleKeyDown}
            isLoadingReply={isLoadingReply}
          />
        </main>
      </div>
    </div>
  );
}
