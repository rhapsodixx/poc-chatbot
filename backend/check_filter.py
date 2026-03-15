import asyncio
from app.services.vectorstore import get_collection

async def main():
    collection = get_collection()
    res = collection.query(
        query_texts=["Dadi Bali Adventure"], 
        n_results=2, 
        where={"url": {"$contains": "/catalog/"}}
    )
    if not res["documents"] or not res["documents"][0]:
        print("No results found.")
        return

    for meta, doc in zip(res["metadatas"][0], res["documents"][0]):
        print(f"URL from meta: {meta.get('url')}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
