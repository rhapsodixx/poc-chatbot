import { ChatWidget } from "@/components/chat-widget";
import { Ticket, Map, Headset } from "lucide-react";
import { IngestButton } from "@/components/admin/ingest-button";

export default function Home() {
  return (
    <main className="min-h-[100dvh] bg-slate-50 relative flex flex-col pt-8 pb-12 md:pt-20 px-4">
      {/* Decorative Background Elements (Aurora UI Style) contained safely */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-violet-200/40 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-cyan-200/30 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-6xl w-full mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-8 lg:mb-0 z-10">
        {/* Left Side: Marketing / Context */}
        <div className="flex flex-col gap-6 text-center lg:text-left">
          <div className="inline-flex w-fit mx-auto lg:mx-0 items-center rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-sm font-medium text-violet-800">
            <span className="flex h-2 w-2 rounded-full bg-violet-500 mr-2"></span>
            AI-Powered Support
          </div>
          <h1 className="text-4xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-tight">
            Discover Your Next <br className="hidden lg:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-cyan-500">
              Adventure
            </span>
          </h1>
          <p className="text-lg text-slate-600 max-w-lg mx-auto lg:mx-0">
            Get instant answers about attractions, book tickets effortlessly, and plan your perfect itinerary with our intelligent concierge.
          </p>

          <div className="flex flex-col gap-4 mt-4">
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto lg:mx-0">
              <div className="bg-violet-100 text-violet-600 p-2 rounded-lg"><Ticket size={20} /></div>
              <span className="font-medium">Real-time Ticket Pricing</span>
            </div>
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto lg:mx-0">
              <div className="bg-cyan-100 text-cyan-600 p-2 rounded-lg"><Map size={20} /></div>
              <span className="font-medium">Curated Micro-Itineraries</span>
            </div>
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto lg:mx-0">
              <div className="bg-emerald-100 text-emerald-600 p-2 rounded-lg"><Headset size={20} /></div>
              <span className="font-medium">Seamless Human Handoff</span>
            </div>
          </div>
        </div>

        {/* Right Side: Chat Widget */}
        <div className="w-full flex flex-col items-center justify-center gap-4">
          <ChatWidget />
          <div className="w-full flex justify-center lg:justify-end pr-2">
            <IngestButton modelName={process.env.OPENROUTER_PRIMARY_MODEL || "Unknown Model"} />
          </div>
        </div>
      </div>
    </main>
  );
}
