"use client";

import { useState, useEffect } from "react";
import { RefreshCw, CheckCircle2, AlertCircle, Bot } from "lucide-react";

export function IngestButton({ modelName = "Unknown Model" }: { modelName?: string }) {
  const [status, setStatus] = useState<"idle" | "running" | "completed" | "failed">("idle");
  const [result, setResult] = useState<any>(null);

  const startIngestion = async () => {
    setStatus("running");
    setResult(null);
    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
      });
      const data = await res.json();
      if (data.status === "already_running") {
        setStatus("running");
      }
    } catch (error) {
      console.error(error);
      setStatus("failed");
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (status === "running") {
      interval = setInterval(async () => {
        try {
          const res = await fetch("/api/ingest/status");
          const data = await res.json();
          
          if (data.status === "completed") {
            setStatus("completed");
            setResult(data.last_result);
            clearInterval(interval);
          } else if (data.status === "failed") {
            setStatus("failed");
            setResult(data.last_result);
            clearInterval(interval);
          }
        } catch (error) {
          console.error("Error polling status:", error);
        }
      }, 3000); // poll every 3 seconds
    }

    return () => clearInterval(interval);
  }, [status]);

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={startIngestion}
        disabled={status === "running"}
        className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all shadow-sm
          ${status === "running" ? "bg-slate-100 text-slate-400 cursor-not-allowed" : 
            "bg-white border border-violet-200 text-violet-700 hover:bg-violet-50 hover:shadow-md"}`}
      >
        <RefreshCw className={`w-4 h-4 ${status === "running" ? "animate-spin text-slate-400" : "text-violet-500"}`} />
        {status === "running" ? "Syncing Knowledge Base..." : "Sync Knowledge Base"}
      </button>

      {status === "idle" && (
        <div className="flex items-center gap-1.5 mt-[-4px] text-[11px] font-medium text-slate-500 bg-white/60 px-2.5 py-1 rounded-full border border-slate-200/60 shadow-sm backdrop-blur-sm transition-all hover:bg-white/80 hover:border-violet-200 hover:text-violet-600">
          <Bot size={12} className="text-violet-500" />
          Powered by <span className="font-semibold text-slate-700">{modelName}</span>
        </div>
      )}

      {status === "completed" && (
        <div className="flex flex-col items-center text-sm text-emerald-600 bg-emerald-50 px-3 py-2 rounded-md border border-emerald-100">
          <div className="flex items-center gap-2 font-medium">
            <CheckCircle2 className="w-4 h-4" />
            Sync Complete
          </div>
          {result && (
            <div className="text-xs text-emerald-700/80 mt-1 mt-1 text-center">
              {result.pages_processed} pages processed • {result.chunks_upserted} chunks loaded • {result.stale_urls_removed || 0} stale URLs removed
            </div>
          )}
        </div>
      )}

      {status === "failed" && (
        <div className="flex flex-col items-center text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md border border-red-100">
          <div className="flex items-center gap-2 font-medium">
            <AlertCircle className="w-4 h-4" />
            Sync Failed
          </div>
          <div className="text-xs text-red-700/80 mt-1 max-w-[200px] text-center truncate" title={result?.error}>
            {result?.error || "Unknown error occurred"}
          </div>
        </div>
      )}
    </div>
  );
}
