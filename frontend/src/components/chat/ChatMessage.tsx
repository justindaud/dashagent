"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  return (
    <div className={`flex ${message.role === "user" ? "justify-end" : ""}`}>
      <div
        className={`px-4 py-3 rounded-xl max-w-[85%] sm:max-w-[75%] md:max-w-lg min-w-0 ${
          message.role === "user" ? "bg-primary/10 text-primary" : ""
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
    </div>
  );
};
