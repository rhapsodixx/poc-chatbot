import React from "react";
import { ProductCard, type Product } from "./product-card";
import { CardCarousel } from "./card-carousel";

export interface Activity {
  time: string;
  title: string;
  description: string;
  products?: Product[];
}

export interface ItineraryDay {
  day: number;
  title: string;
  activities: Activity[];
}

export interface ItineraryData {
  itinerary: ItineraryDay[];
}

export function ItineraryTimeline({ data }: { data: ItineraryData }) {
  if (!data || !data.itinerary || data.itinerary.length === 0) return null;

  return (
    <div className="flex flex-col gap-6 w-full py-2">
      <div className="mb-2 text-center">
        <h3 className="text-[17px] font-semibold text-slate-800 tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-violet-600 to-indigo-600">
          Your Perfect Trip
        </h3>
        <p className="text-[13px] text-slate-500 mt-1">Carefully planned for you</p>
      </div>

      <div className="relative border-l border-slate-200/60 ml-4 space-y-8 pb-4">
        {data.itinerary.map((day, dayIdx) => (
          <div key={dayIdx} className="relative pl-6">
            {/* Day indicator node */}
            <div className="absolute -left-[1.35rem] top-0 h-10 w-10 rounded-full bg-white border border-slate-200/60 shadow-sm flex items-center justify-center">
              <span className="text-sm font-bold bg-clip-text text-transparent bg-gradient-to-br from-violet-500 to-cyan-400">
                Day {day.day}
              </span>
            </div>

            <div className="mb-4 pt-2 pl-3">
              <h4 className="text-[15px] font-semibold text-slate-800">{day.title}</h4>
            </div>

            <div className="flex flex-col gap-5 pl-2">
              {day.activities.map((activity, actIdx) => (
                <div key={actIdx} className="relative">
                  {/* Activity node */}
                  <div className="absolute -left-[27px] top-3 h-2 w-2 rounded-full bg-cyan-400 ring-4 ring-white" />
                  
                  <div className="bg-white/80 border border-slate-100/80 shadow-sm rounded-2xl p-4 flex flex-col gap-2 hover:shadow-md hover:border-violet-100/60 transition-all duration-300">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-bold text-violet-600 bg-violet-50 px-2.5 py-1 rounded-md tracking-wide">
                        {activity.time}
                      </span>
                      <h5 className="font-semibold text-slate-800 text-[14px] leading-snug">
                        {activity.title}
                      </h5>
                    </div>
                    
                    {activity.description && (
                      <p className="text-[13px] text-slate-600 leading-relaxed mt-1">
                        {activity.description}
                      </p>
                    )}

                    {activity.products && activity.products.length > 0 && (
                      <div className="mt-3 -mx-1">
                        {activity.products.length === 1 ? (
                          <ProductCard product={activity.products[0]} />
                        ) : (
                          <CardCarousel products={activity.products} />
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
