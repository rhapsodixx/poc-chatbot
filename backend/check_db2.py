import asyncio
from app.services.vectorstore import query_similar

async def main():
    res = await query_similar("Create me an itinerary for 2 days in Bali", n_results=10)
    for meta, doc in zip(res["metadatas"][0], res["documents"][0]):
        print(f"URL: {meta.get('url')}")
        print(f"TITLE: {meta.get('title')}")
        # print first 100 chars
        print(f"DOC: {doc[:150]}...")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
