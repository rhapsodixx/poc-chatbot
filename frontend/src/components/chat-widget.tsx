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
import { ProductCard, type Product } from "./product-card";
import { CardCarousel } from "./card-carousel";
function parseMessageContent(content: string) {
  try {
    // 1. Try to find content between ```json and ```
    const markdownMatch = content.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
    if (markdownMatch) {
      const parsed = JSON.parse(markdownMatch[1].trim());
      if (parsed?.products) {
        return { text: content.replace(markdownMatch[0], "").trim(), products: parsed.products as Product[] };
      }
    }

    // 2. Try to find content between ```json and end of string (if truncated closing ticks)
    const truncatedMarkdownMatch = content.match(/```(?:json)?\s*(\{[\s\S]*)$/i);
    if (truncatedMarkdownMatch) {
      let jsonStr = truncatedMarkdownMatch[1];
      try {
        const parsed = JSON.parse(jsonStr);
        if (parsed?.products) {
          return { text: content.replace(truncatedMarkdownMatch[0], "").trim(), products: parsed.products as Product[] };
        }
      } catch (e) {
        // Attempt aggressive fix for incomplete JSON (e.g., missing closing braces/brackets)
        try {
          const aggressiveFix = jsonStr.trim().replace(/,$/, "") + "]}";
          const parsed2 = JSON.parse(aggressiveFix);
          if (parsed2?.products) {
            return { text: content.replace(truncatedMarkdownMatch[0], "").trim(), products: parsed2.products as Product[] };
          }
        } catch (e2) {}
      }
    }

    // 3. Fallback: try to find any { "products": ... } at the end
    const fallbackMatch = content.match(/\{\s*"products"\s*:[\s\S]*?\}\s*$/i);
    if (fallbackMatch) {
      const parsed = JSON.parse(fallbackMatch[0]);
      if (parsed?.products) {
        return { text: content.replace(fallbackMatch[0], "").trim(), products: parsed.products as Product[] };
      }
    }
  } catch (e) {
    console.error("Failed to parse product JSON", e);
  }
  
  // Clean up any stray ```json at the end if we failed to parse anything useful
  const cleanedText = content.replace(/```(?:json)?\s*(\{[\s\S]*)?$/i, "").trim();
  return { text: cleanedText || content, products: null };
}
type HandoffPayload = {
  type: string;
  message: string;
  email_url?: string;
  whatsapp_url?: string;
};

type Message = {
  id: string;
  role: "user" | "bot";
  content: string;
  handoff?: HandoffPayload;
  tokensUsed?: number;
  cost?: number;
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
        tokensUsed: data.tokens_used,
        cost: data.cost,
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
    <Card className="w-full max-w-lg mx-auto shadow-2xl border border-violet-100/50 ring-0 bg-white/80 backdrop-blur-xl overflow-hidden rounded-2xl flex flex-col h-[750px] max-h-[90vh] sm:max-h-[850px] p-0 gap-0">
      <CardHeader className="bg-gradient-to-r from-violet-600 to-indigo-600 text-white p-4 shrink-0 shadow-[0_4px_20px_-5px_rgba(124,58,237,0.3)] relative overflow-hidden m-0 border-b-0 space-y-0 text-left">
        {/* Subtle background glow effect for header */}
        <div className="absolute top-[-50%] right-[-10%] w-48 h-48 bg-cyan-400/30 rounded-full blur-3xl pointer-events-none mix-blend-screen" />
        
        <div className="flex items-center gap-3 relative z-10">
          <Avatar className="h-10 w-10 border-2 border-white/20 shadow-sm bg-white/10 backdrop-blur-md">
            <AvatarFallback className="bg-transparent text-white"><Bot size={20} /></AvatarFallback>
          </Avatar>
          <div>
            <CardTitle className="text-lg font-semibold tracking-tight">Satusatu Concierge</CardTitle>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400"></span>
              </span>
              <p className="text-xs text-violet-100 font-medium tracking-wide">Always online to help</p>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 flex-1 overflow-hidden">
        <ScrollArea className="h-full p-4 bg-slate-50/30">
          <div className="flex flex-col gap-5 pb-4">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 15, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
                  className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                >
                  <Avatar className="h-8 w-8 shrink-0 mt-1 shadow-sm border border-slate-100">
                    {msg.role === "user" ? (
                      <AvatarFallback className="bg-slate-100 text-slate-600">
                        <User size={15} />
                      </AvatarFallback>
                    ) : (
                      <AvatarFallback className="bg-violet-600 text-white">
                        <Bot size={15} />
                      </AvatarFallback>
                    )}
                  </Avatar>

                  <div
                    className={`flex flex-col gap-2 max-w-[85%] ${
                      msg.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    {(() => {
                      const { text, products } = parseMessageContent(msg.content);
                      const hasProducts = products && products.length > 0;
                      return (
                        <div
                          className={`px-4 py-3 text-[15px] shadow-sm flex flex-col gap-4 font-medium leading-relaxed tracking-tight ${
                            hasProducts ? "rounded-t-2xl rounded-br-2xl w-full min-w-[280px] sm:min-w-[360px]" : "rounded-2xl"
                          } ${
                            msg.role === "user"
                              ? "bg-slate-800 text-white rounded-tr-none shadow-md"
                              : "bg-white text-slate-700 border border-slate-200/60 rounded-tl-none shadow-sm"
                          }`}
                        >
                          {text && <div className={`whitespace-pre-wrap flex-1 ${hasProducts ? "mb-3" : ""}`}>{text}</div>}
                          {hasProducts && (
                            <div className="w-full -mx-1">
                              {products.length === 1 ? (
                                <ProductCard product={products[0]} />
                              ) : (
                                <CardCarousel products={products} />
                              )}
                            </div>
                          )}
                          {msg.role === "bot" && msg.tokensUsed ? (
                            <div className="text-[10px] text-slate-400 font-medium tracking-wide mt-1.5 self-end flex items-center gap-1 opacity-80 backdrop-blur-sm select-none">
                              <span>⚡ {msg.tokensUsed} tokens</span>
                              <span>•</span>
                              <span>${msg.cost?.toFixed(5)}</span>
                            </div>
                          ) : null}
                        </div>
                      );
                    })()}

                    {msg.handoff && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 5 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        className="bg-cyan-50/50 border border-cyan-100/50 rounded-2xl p-4 shadow-sm w-full mt-1 backdrop-blur-sm"
                      >
                        <p className="text-xs text-cyan-800 font-semibold mb-3 flex items-center gap-1.5 uppercase tracking-wider">
                          <Headset size={14} /> Connect with Human
                        </p>
                        <div className="flex flex-col gap-2.5">
                          {msg.handoff.email_url && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full justify-between bg-white hover:bg-slate-50 text-slate-700 border-slate-200 h-10 rounded-xl font-medium"
                              onClick={() => window.location.href = msg.handoff!.email_url as string}
                            >
                              Email Support
                              <ExternalLink size={14} className="text-slate-400" />
                            </Button>
                          )}
                          {msg.handoff.whatsapp_url && (
                            <Button
                              variant="default"
                              size="sm"
                              className="w-full justify-between bg-emerald-500 hover:bg-emerald-600 text-white h-10 rounded-xl font-medium shadow-sm"
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
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 flex-row"
              >
                <Avatar className="h-8 w-8 shrink-0 mt-1 border border-violet-100">
                  <AvatarFallback className="bg-violet-600 text-white">
                    <Bot size={15} />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-white border border-slate-200/60 text-slate-800 px-5 py-3.5 rounded-2xl rounded-tl-none shadow-sm flex gap-1.5 items-center max-w-[fit-content]">
                  <motion.div
                    className="w-1.5 h-1.5 bg-violet-400 rounded-full"
                    animate={{ y: [0, -4, 0], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut", delay: 0 }}
                  />
                  <motion.div
                    className="w-1.5 h-1.5 bg-violet-400 rounded-full"
                    animate={{ y: [0, -4, 0], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut", delay: 0.15 }}
                  />
                  <motion.div
                    className="w-1.5 h-1.5 bg-violet-400 rounded-full"
                    animate={{ y: [0, -4, 0], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut", delay: 0.3 }}
                  />
                </div>
              </motion.div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>
      </CardContent>
      
      <div className="p-3 bg-white/90 backdrop-blur-md border-t border-slate-100 z-10 shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex w-full items-center gap-2 relative"
        >
          <Input
            placeholder="Ask about tickets or itineraries..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            className="flex-1 border-slate-200 focus-visible:ring-0 focus-visible:ring-offset-0 focus:border-violet-500 rounded-2xl bg-slate-50/50 h-12 px-4 shadow-sm text-[15px] pr-12 transition-all"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || isLoading}
            className="absolute right-1.5 top-1.5 bottom-1.5 bg-violet-600 hover:bg-violet-700 rounded-xl h-9 w-9 shadow-sm transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
          >
            <Send size={16} className={input.trim() && !isLoading ? "text-white" : "text-violet-200"} />
            <span className="sr-only">Send</span>
          </Button>
        </form>
      </div>
    </Card>
  );
}
