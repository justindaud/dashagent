"use client";

import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Check, Edit } from "lucide-react";

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

interface ConversationItemProps {
  conv: Conversation;
  isActive: boolean;
  isEditing: boolean;
  editingTitle: string;
  setEditingTitle: (title: string) => void;
  onSaveEdit: () => void;
  onStartEdit: (id: string, currentTitle: string) => void;
  onSelect: (id: string) => void;
  isSidebarCollapsed: boolean;
}

export const ConversationItem = ({
  conv,
  isActive,
  isEditing,
  editingTitle,
  setEditingTitle,
  onSaveEdit,
  onStartEdit,
  onSelect,
  isSidebarCollapsed,
}: ConversationItemProps) => {
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
  );
};
