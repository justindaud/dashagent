"use client";

import { useState, useEffect, useRef } from "react";
import api from "@/lib/axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import TextareaAutosize from "react-textarea-autosize";
import { Header } from "@/components/dashboard/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Bot, User, Plus, Menu, Send, Edit, Check, Loader2 } from "lucide-react";

// Message and conversation types
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

const ConversationItem = ({
  conv,
  isActive,
  isEditing,
  editingTitle,
  setEditingTitle,
  onSaveEdit,
  onStartEdit,
  onSelect,
  isSidebarCollapsed,
}: {
  conv: Conversation;
  isActive: boolean;
  isEditing: boolean;
  editingTitle: string;
  setEditingTitle: (title: string) => void;
  onSaveEdit: () => void;
  onStartEdit: (id: string, currentTitle: string) => void;
  onSelect: (id: string) => void;
  isSidebarCollapsed: boolean;
}) => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") onSaveEdit();
    if (e.key === "Escape") onStartEdit("", "");
  };

  if (isEditing && !isSidebarCollapsed) {
    return (
      <div className="flex items-center gap-2 px-3 py-1">
        <Input
          autoFocus
          value={editingTitle}
          onChange={(e) => setEditingTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={onSaveEdit}
          className="h-8 flex-1"
        />
        <Button size="icon" className="h-8 w-8 flex-shrink-0" onClick={onSaveEdit}>
          <Check size={16} />
        </Button>
      </div>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={() => onSelect(conv.session_id)}
          className={`group w-full text-left p-3 rounded-md text-sm flex items-center gap-3 transition-colors ${
            isActive ? "bg-primary/10 text-primary font-semibold" : "hover:bg-gray-100"
          } ${isSidebarCollapsed && "justify-center"}`}
        >
          <span className={`truncate flex-1 ${isSidebarCollapsed ? "hidden" : "block"}`}>{conv.title}</span>
          {!isSidebarCollapsed && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => {
                e.stopPropagation();
                onStartEdit(conv.session_id, conv.title);
              }}
            >
              <Edit size={14} />
            </Button>
          )}
        </button>
      </TooltipTrigger>
      {isSidebarCollapsed && <TooltipContent side="right">{conv.title}</TooltipContent>}
    </Tooltip>
  );
};

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
      const response = await api.get("/api/sessions");
      const fetchedSessions = (response.data.data || []).map((s: any) => ({ ...s, messages: [] }));
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
      const response = await api.post("/api/sessions", {});
      const newSessionData = response.data.data[0];
      const newConversation: Conversation = {
        session_id: newSessionData.session_id,
        title: newSessionData.title_suggestion,
        messages: [{ role: "assistant", content: "Hello! How can I help you analyze your hotel data today?" }],
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
      const response = await api.get(`/api/sessions/${sessionId}/messages`);
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
      await api.post(`/api/sessions/${activeConversationId}/run`, {
        user_input: messageToSend,
      });
      await fetchMessagesForSession(activeConversationId);
    } catch (error) {
      console.error("Error sending chat message:", error);
      setConversations((prev) =>
        prev.map((convo) => {
          if (convo.session_id === activeConversationId) {
            return { ...convo, messages: [...convo.messages, { role: "assistant", content: "Sorry, an error occurred." }] };
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
      await api.put(`/api/sessions/${editingConversationId}`, { title: editingTitle });
      setConversations((prev) => prev.map((c) => (c.session_id === editingConversationId ? { ...c, title: editingTitle } : c)));
    } catch (error) {
      console.error("Failed to update title", error);
    } finally {
      setEditingConversationId(null);
      setEditingTitle("");
    }
  };

  // Responsive Sidebar Content for Desktop and Mobile
  const DesktopSidebarContent = () => (
    <TooltipProvider delayDuration={0}>
      <div className="p-4 space-y-4">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button onClick={handleNewChat} className="w-full">
              <Plus className={`h-4 w-4 ${!isDesktopSidebarCollapsed && "mr-2"}`} />
              <span className={isDesktopSidebarCollapsed ? "hidden" : ""}>New Chat</span>
            </Button>
          </TooltipTrigger>
          {isDesktopSidebarCollapsed && <TooltipContent side="right">New Chat</TooltipContent>}
        </Tooltip>
      </div>
      <div className="flex-1 overflow-y-auto px-2">
        <p
          className={`text-xs font-semibold text-gray-500 uppercase mb-2 transition-opacity ${
            isDesktopSidebarCollapsed ? "opacity-0" : "opacity-100 px-3"
          }`}
        >
          Recent
        </p>
        <nav className="space-y-1">
          {isLoadingConversations ? (
            <div className="space-y-2 px-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : (
            conversations.map((conv) => (
              <ConversationItem
                key={conv.session_id}
                conv={conv}
                isActive={activeConversationId === conv.session_id}
                isEditing={editingConversationId === conv.session_id}
                editingTitle={editingTitle}
                setEditingTitle={setEditingTitle}
                onSaveEdit={handleUpdateTitle}
                onStartEdit={handleStartEdit}
                onSelect={handleSelectConversation}
                isSidebarCollapsed={isDesktopSidebarCollapsed}
              />
            ))
          )}
        </nav>
      </div>
    </TooltipProvider>
  );

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <div className="hidden md:block">
        <Header page="chat" />
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div
          className={`hidden md:flex flex-col bg-white border-r transition-all duration-300 ease-in-out ${
            isDesktopSidebarCollapsed ? "w-20" : "w-72"
          }`}
          onMouseEnter={() => !editingConversationId && setIsDesktopSidebarCollapsed(false)}
          onMouseLeave={() => !editingConversationId && setIsDesktopSidebarCollapsed(true)}
        >
          <DesktopSidebarContent />
        </div>

        <main className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 ">
            <div className="md:hidden flex items-center gap-2 pb-2 border-b">
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

            {activeConversation?.isLoadingMessages ? (
              <div className="flex justify-center items-center h-full">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              activeConversation?.messages.map((message, index) => (
                <div key={index} className={`flex items-start gap-4 ${message.role === "user" ? "justify-end" : ""}`}>
                  {message.role === "assistant" && (
                    <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-700">
                      <Bot size={18} />
                    </span>
                  )}
                  <div
                    className={`px-4 py-3 rounded-xl max-w-[85%] sm:max-w-[75%] md:max-w-lg min-w-0 ${
                      message.role === "user" ? "bg-primary/10 text-primary-foreground" : "bg-white shadow-sm"
                    }`}
                  >
                    <div className="prose prose-sm max-w-none prose-p:my-0 prose-h3:my-2 break-words">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          table: ({ node, ...props }) => (
                            <div className="w-full overflow-x-auto my-2 rounded-md border">
                              <table {...props} className="my-0" />
                            </div>
                          ),
                          pre: ({ node, ...props }) => (
                            <div className="overflow-x-auto rounded-md bg-gray-900 text-white p-4 my-2">
                              <pre {...props} className="bg-transparent p-0 my-0" />
                            </div>
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                  {message.role === "user" && (
                    <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-primary text-primary-foreground">
                      <User size={18} />
                    </span>
                  )}
                </div>
              ))
            )}
            {isLoadingReply && (
              <div className="flex flex-col items-start gap-2">
                <div className="flex items-start gap-4">
                  <span className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-700">
                    <Bot size={18} />
                  </span>
                  <div className="px-4 py-3 rounded-lg bg-white shadow-sm flex items-center">
                    <span className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s] mx-1"></span>
                    <span className="h-2 w-2 bg-primary rounded-full animate-bounce"></span>
                  </div>
                </div>
                <div className="pl-12">
                  <p className="text-xs text-gray-500 italic">AI has been thinking for {timer}s</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 md:p-6 ">
            <form ref={formRef} onSubmit={handleChatSubmit} className="flex gap-2 items-end max-w-4xl mx-auto">
              <TextareaAutosize
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about revenue, occupancy, guest segments..."
                className="flex-1 resize-none rounded-lg border border-gray-300 bg-background px-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                minRows={1}
                maxRows={5}
              />
              <Button type="submit" size="icon" className="flex-shrink-0" disabled={isLoadingReply || !chatMessage.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <p className="text-xs text-gray-500 mt-2 text-center">DashAgent AI can make mistakes. Consider checking important information.</p>
          </div>
        </main>
      </div>
    </div>
  );
}
