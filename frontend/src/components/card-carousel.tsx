import React from "react";
import { ProductCard, type Product } from "./product-card";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

export function CardCarousel({ products }: { products: Product[] }) {
  if (!products || products.length === 0) return null;

  return (
    <div className="w-full -mx-4 px-4 sm:mx-0 sm:px-0 mt-2 mb-1">
      <ScrollArea className="w-[calc(100vw-2rem)] sm:w-full whitespace-nowrap pb-4">
        <div className="flex w-max gap-3">
          {products.map((product, idx) => (
            <ProductCard key={idx} product={product} />
          ))}
        </div>
        <ScrollBar orientation="horizontal" className="h-1.5 opacity-50 transition-opacity hover:opacity-100" />
      </ScrollArea>
    </div>
  );
}
