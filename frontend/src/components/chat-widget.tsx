"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Ticket, Map, Headset, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

type HandoffPayload = {
  type: string;
  message: string;
  freshdesk_url?: string;
  whatsapp_url?: string;
};

type Message = {
  id: string;
  role: "user" | "bot";
  content: string;
  handoff?: HandoffPayload;
};

export function ChatWidget() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "bot",
      content: "Hello! I'm your satusatu.com concierge. How can I help you plan your next adventure today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg.content,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) throw new Error("API error");

      const data = await response.json();
      setConversationId(data.conversation_id);

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "bot",
        content: data.reply,
        handoff: data.handoff,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "bot",
          content: "Sorry, I'm having trouble connecting to the server. Please try again later.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto shadow-2xl border-white/20 bg-white/70 backdrop-blur-xl overflow-hidden ring-1 ring-sky-100">
      <CardHeader className="bg-gradient-to-r from-sky-500 to-sky-400 text-white p-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10 border-2 border-white shadow-sm">
            <AvatarImage src="/bot-avatar.png" alt="SatuSatu Bot" />
            <AvatarFallback className="bg-orange-500 text-white"><Bot size={20} /></AvatarFallback>
          </Avatar>
          <div>
            <CardTitle className="text-lg font-bold">satusatu Concierge</CardTitle>
            <p className="text-sm opacity-90 leading-tight">Always online to help you explore</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <ScrollArea className="h-[450px] p-4 bg-slate-50/50">
          <div className="flex flex-col gap-4">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.2 }}
                  className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                >
                  <Avatar className="h-8 w-8 shrink-0 mt-1 shadow-sm">
                    {msg.role === "user" ? (
                      <AvatarFallback className="bg-slate-200 text-slate-700">
                        <User size={16} />
                      </AvatarFallback>
                    ) : (
                      <AvatarFallback className="bg-sky-500 text-white">
                        <Bot size={16} />
                      </AvatarFallback>
                    )}
                  </Avatar>

                  <div
                    className={`flex flex-col gap-2 max-w-[80%] ${
                      msg.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    <div
                      className={`px-4 py-2 rounded-2xl text-sm shadow-sm ${
                        msg.role === "user"
                          ? "bg-slate-800 text-white rounded-tr-none"
                          : "bg-white text-slate-800 border border-slate-100 rounded-tl-none"
                      }`}
                    >
                      {msg.content}
                    </div>

                    {msg.handoff && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-orange-50 border border-orange-100 rounded-xl p-3 shadow-sm w-full mt-1"
                      >
                        <p className="text-xs text-orange-800 font-medium mb-2 flex items-center gap-1">
                          <Headset size={14} /> Connect with Human Support
                        </p>
                        <div className="flex flex-col gap-2">
                          {msg.handoff.freshdesk_url && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full justify-between bg-white hover:bg-slate-50 text-slate-700 border-slate-200"
                              onClick={() => window.open(msg.handoff!.freshdesk_url, "_blank")}
                            >
                              Open Support Ticket
                              <ExternalLink size={14} className="text-slate-400" />
                            </Button>
                          )}
                          {msg.handoff.whatsapp_url && (
                            <Button
                              variant="default"
                              size="sm"
                              className="w-full justify-between bg-emerald-500 hover:bg-emerald-600 text-white"
                              onClick={() => window.open(msg.handoff!.whatsapp_url, "_blank")}
                            >
                              Chat on WhatsApp
                              <ExternalLink size={14} className="opacity-70" />
                            </Button>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3 flex-row"
              >
                <Avatar className="h-8 w-8 shrink-0 mt-1">
                  <AvatarFallback className="bg-sky-500 text-white">
                    <Bot size={16} />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-white border border-slate-100 text-slate-800 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm flex gap-1 items-center">
                  <motion.div
                    className="w-2 h-2 bg-sky-400 rounded-full"
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-sky-400 rounded-full"
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-sky-400 rounded-full"
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                  />
                </div>
              </motion.div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      </CardContent>

      <Separator />
      
      <CardFooter className="p-3 bg-white/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex w-full items-center gap-2"
        >
          <Input
            placeholder="Ask about tickets or itineraries..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            className="flex-1 border-slate-200 focus-visible:ring-sky-500 rounded-full bg-slate-50/50"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="bg-sky-500 hover:bg-sky-600 rounded-full shrink-0 h-10 w-10 shadow-sm transition-all"
          >
            <Send size={18} className={input.trim() && !isLoading ? "text-white" : "text-sky-100"} />
            <span className="sr-only">Send</span>
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
}
