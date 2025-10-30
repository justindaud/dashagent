"use client";

import TextareaAutosize from "react-textarea-autosize";
import { Button } from "../ui/button";
import { Send } from "lucide-react";
import { RefObject } from "react";

interface ChatInputProps {
  formRef: RefObject<HTMLFormElement>;
  chatMessage: string;
  setChatMessage: (value: string) => void;
  handleChatSubmit: (e: React.FormEvent) => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  isLoadingReply: boolean;
}

export const ChatInput = ({ formRef, chatMessage, setChatMessage, handleChatSubmit, handleKeyDown, isLoadingReply }: ChatInputProps) => {
  return (
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
  );
};
