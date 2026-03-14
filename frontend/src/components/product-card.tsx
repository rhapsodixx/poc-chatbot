import React from "react";
import { MapPin, Star } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export interface ProductPriceOptions {
  original?: string;
  current: string;
  discountBadge?: string;
}

export interface Product {
  imageUrl?: string;
  location?: string;
  title: string;
  rating?: string;
  reviewsCount?: string;
  soldCount?: string;
  priceOptions: ProductPriceOptions;
  productUrl?: string;
}

export function ProductCard({ product }: { product: Product }) {
  return (
    <a
      href={product.productUrl || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="block w-full sm:w-[280px] shrink-0 overflow-hidden rounded-2xl bg-white/90 backdrop-blur-sm shadow-[0_2px_15px_-3px_rgba(0,0,0,0.07),0_10px_20px_-2px_rgba(0,0,0,0.04)] border border-violet-100/50 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:border-cyan-300/50 hover:-translate-y-0.5 transition-all duration-300 group cursor-pointer"
    >
      <div className="relative h-44 w-full bg-slate-100 overflow-hidden">
        {product.imageUrl ? (
          <img
            src={product.imageUrl}
            alt={product.title}
            className="w-full h-full object-cover transition-transform group-hover:scale-105 duration-500 ease-out"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-400 bg-slate-200">
            No image
          </div>
        )}
        
        {/* Subtle gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 via-slate-900/10 to-transparent opacity-60" />

        {product.location && (
          <div className="absolute top-3 left-3 bg-black/40 backdrop-blur-md text-white text-[11px] font-medium tracking-wide px-2.5 py-1 rounded-full flex items-center shadow-sm border border-white/10">
            <MapPin size={10} className="mr-1 text-cyan-400" />
            {product.location}
          </div>
        )}
      </div>

      <div className="p-4 flex flex-col gap-3 relative">
        <div className="space-y-1">
          <h3 className="font-semibold text-slate-800 leading-snug line-clamp-2 text-[15px] group-hover:text-violet-700 transition-colors">
            {product.title}
          </h3>

          <div className="flex items-center text-xs text-slate-500 gap-1.5 font-medium">
            {product.rating && (
              <div className="flex items-center text-slate-700">
                <Star size={12} className="fill-cyan-500 text-cyan-500 mr-1" />
                <span>{product.rating}</span>
              </div>
            )}
            {product.reviewsCount && (
              <span className="opacity-75">({product.reviewsCount})</span>
            )}
            {(product.rating || product.reviewsCount) && product.soldCount && (
              <span className="text-slate-300">•</span>
            )}
            {product.soldCount && <span className="opacity-75">{product.soldCount} sold</span>}
          </div>
        </div>

        <div className="mt-2 pt-3 border-t border-slate-100/80 flex items-end justify-between gap-2">
          <div className="flex flex-col gap-0.5">
            <div className="text-[11px] text-slate-500 font-medium tracking-tight h-3 flex items-center">
              from
            </div>
            <div className="text-violet-700 text-[18px] font-bold leading-none tracking-tight">
              {product.priceOptions.current}
            </div>
            
            {(product.priceOptions.original || product.priceOptions.discountBadge) && (
              <div className="flex items-center gap-2 mt-1">
                {product.priceOptions.original && (
                  <span className="text-[11px] text-slate-400 line-through font-medium decorat">
                    {product.priceOptions.original}
                  </span>
                )}
                {product.priceOptions.discountBadge && (
                  <span className="bg-cyan-100/80 text-cyan-800 text-[10px] font-bold px-1.5 py-0.5 rounded-md leading-none uppercase tracking-wider flex items-center">
                    {product.priceOptions.discountBadge}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </a>
  );
}
