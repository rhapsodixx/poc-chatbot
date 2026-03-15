import asyncio
from app.services.vectorstore import query_similar

async def main():
    res = await query_similar("ATV Quad Bike Adventure", n_results=5)
    if not res["documents"] or not res["documents"][0]:
        print("No results found.")
        return

    for meta, doc in zip(res["metadatas"][0], res["documents"][0]):
        print(f"URL: {meta.get('url')}")
        print(f"TITLE: {meta.get('title')}")
        print(f"DOC SNIPPET: {doc[:150]}...")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
