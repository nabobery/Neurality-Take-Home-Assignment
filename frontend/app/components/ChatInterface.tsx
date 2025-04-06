"use client";

import { useState } from "react";
import { Send, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { NEXT_PUBLIC_API_BASE_URL } from "@/app/config";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: "user" as const, content: input };
    const currentMessages = [...messages, userMessage];
    setMessages(currentMessages);
    setInput("");
    setLoading(true);

    try {
      // const chatHistory = currentMessages
      //   .filter((msg) => msg.role === "assistant")
      //   .map((msg) => msg.content)
      //   .join("\n\n");

      const response = await fetch(NEXT_PUBLIC_API_BASE_URL + "/ask/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: input,
        }),
      });

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to parse error response." }));
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      const data = await response.json();
      const assistantMessage = {
        role: "assistant" as const,
        content: data.answer || "No answer received.",
      };

      setMessages((msgs) => [...msgs, assistantMessage]);
    } catch (error) {
      console.error("Error getting response:", error);
      const errorMessageContent =
        error instanceof Error
          ? error.message
          : "Sorry, I encountered an error processing your request.";
      const errorMessage = {
        role: "assistant" as const,
        content: `Error: ${errorMessageContent}`,
      };
      setMessages((msgs) => [...msgs, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg transition-colors">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`prose dark:prose-invert max-w-[80%] p-3 rounded-lg ${
                  message.role === "user"
                    ? "bg-blue-500 text-white rounded-br-none"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-none"
                }`}
              >
                {message.role === "assistant" ? (
                  <ReactMarkdown
                    components={{
                      a: (props) => (
                        <a
                          {...props}
                          target="_blank"
                          rel="noopener noreferrer"
                        />
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                ) : (
                  message.content
                )}
              </div>
            </motion.div>
          ))}
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg rounded-bl-none">
                <Loader2 className="w-4 h-4 animate-spin dark:text-gray-100" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <form
        onSubmit={handleSubmit}
        className="border-t dark:border-gray-700 p-4 flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 px-4 py-2 border dark:border-gray-700 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400 transition-colors"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
}
