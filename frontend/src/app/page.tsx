import { ChatWidget } from "@/components/chat-widget";
import { Ticket, Map, Headset } from "lucide-react";
import { IngestButton } from "@/components/admin/ingest-button";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 relative overflow-x-hidden flex flex-col items-center p-4 py-12">
      {/* Admin controls - absolute positioned for easy access */}
      <div className="absolute top-4 right-4 z-50">
        <IngestButton />
      </div>

      {/* Decorative Background Elements (Aurora UI Style) */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-violet-200/40 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-cyan-200/30 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center z-10 my-auto">
        {/* Left Side: Marketing / Context */}
        <div className="flex flex-col gap-6 text-center md:text-left">
          <div className="inline-flex w-fit mx-auto md:mx-0 items-center rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-sm font-medium text-violet-800">
            <span className="flex h-2 w-2 rounded-full bg-violet-500 mr-2"></span>
            AI-Powered Support
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-slate-900 leading-tight">
            Discover Your Next <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-cyan-500">
              Adventure
            </span>
          </h1>
          <p className="text-lg text-slate-600 max-w-lg mx-auto md:mx-0">
            Get instant answers about attractions, book tickets effortlessly, and plan your perfect itinerary with our intelligent concierge.
          </p>

          <div className="flex flex-col gap-4 mt-4">
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto md:mx-0">
              <div className="bg-violet-100 text-violet-600 p-2 rounded-lg"><Ticket size={20} /></div>
              <span className="font-medium">Real-time Ticket Pricing</span>
            </div>
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto md:mx-0">
              <div className="bg-cyan-100 text-cyan-600 p-2 rounded-lg"><Map size={20} /></div>
              <span className="font-medium">Curated Micro-Itineraries</span>
            </div>
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto md:mx-0">
              <div className="bg-emerald-100 text-emerald-600 p-2 rounded-lg"><Headset size={20} /></div>
              <span className="font-medium">Seamless Human Handoff</span>
            </div>
          </div>
        </div>

        {/* Right Side: Chat Widget */}
        <div className="w-full flex items-center justify-center">
          <ChatWidget />
        </div>
      </div>
    </main>
  );
}
