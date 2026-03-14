import { ChatWidget } from "@/components/chat-widget";
import { Ticket, Map, Headset } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 relative overflow-hidden flex flex-col items-center justify-center p-4">
      {/* Decorative Background Elements (Aurora UI Style) */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-sky-200/40 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-orange-200/30 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center z-10">
        {/* Left Side: Marketing / Context */}
        <div className="flex flex-col gap-6 text-center md:text-left">
          <div className="inline-flex w-fit mx-auto md:mx-0 items-center rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-sm font-medium text-sky-800">
            <span className="flex h-2 w-2 rounded-full bg-sky-500 mr-2"></span>
            AI-Powered Support
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-slate-900 leading-tight">
            Discover Your Next <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-500 to-sky-600">
              Adventure
            </span>
          </h1>
          <p className="text-lg text-slate-600 max-w-lg mx-auto md:mx-0">
            Get instant answers about attractions, book tickets effortlessly, and plan your perfect itinerary with our intelligent concierge.
          </p>

          <div className="flex flex-col gap-4 mt-4">
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto md:mx-0">
              <div className="bg-sky-100 text-sky-600 p-2 rounded-lg"><Ticket size={20} /></div>
              <span className="font-medium">Real-time Ticket Pricing</span>
            </div>
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto md:mx-0">
              <div className="bg-orange-100 text-orange-600 p-2 rounded-lg"><Map size={20} /></div>
              <span className="font-medium">Curated Micro-Itineraries</span>
            </div>
            <div className="flex items-center gap-3 text-slate-700 bg-white/60 p-3 rounded-xl border border-white/40 shadow-sm backdrop-blur-md w-max mx-auto md:mx-0">
              <div className="bg-emerald-100 text-emerald-600 p-2 rounded-lg"><Headset size={20} /></div>
              <span className="font-medium">Seamless Human Handoff</span>
            </div>
          </div>
        </div>

        {/* Right Side: Chat Widget */}
        <div className="w-full shadow-2xl rounded-2xl ring-1 ring-slate-900/5 bg-white overflow-hidden">
          <ChatWidget />
        </div>
      </div>
    </main>
  );
}
