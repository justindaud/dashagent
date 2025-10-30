"use client";

import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { Plus } from "lucide-react";
import { ConversationItem } from "./ConversationItem";

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

interface DesktopChatSidebarProps {
  isCollapsed: boolean;
  onNewChat: () => void;
  isLoadingConversations: boolean;
  conversations: Conversation[];
  activeConversationId: string | null;
  editingConversationId: string | null;
  editingTitle: string;
  setEditingTitle: (title: string) => void;
  onSaveEdit: () => void;
  onStartEdit: (id: string, currentTitle: string) => void;
  onSelect: (id: string) => void;
}

export const DesktopChatSidebar = ({
  isCollapsed,
  onNewChat,
  isLoadingConversations,
  conversations,
  activeConversationId,
  editingConversationId,
  editingTitle,
  setEditingTitle,
  onSaveEdit,
  onStartEdit,
  onSelect,
}: DesktopChatSidebarProps) => {
  return (
    <>
      <div className="p-4 space-y-4">
        <Button onClick={onNewChat} className="w-full">
          <Plus className={`h-4 w-4 ${!isCollapsed && "mr-2"}`} />
          <span className={isCollapsed ? "hidden" : ""}>New Chat</span>
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto px-2">
        <p className={`text-xs font-semibold text-gray-500 uppercase mb-2 transition-opacity ${isCollapsed ? "opacity-0" : "opacity-100 px-3"}`}>
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
                onSaveEdit={onSaveEdit}
                onStartEdit={onStartEdit}
                onSelect={onSelect}
                isSidebarCollapsed={isCollapsed}
              />
            ))
          )}
        </nav>
      </div>
    </>
  );
};
