import asyncio
from app.services.vectorstore import query_similar, get_all_stored_metadata

async def main():
    metadata = get_all_stored_metadata()
    homepage_urls = set()
    for url, meta in metadata.items():
        if "/catalog/" not in url:
            homepage_urls.add(url)
    
    print("Non-catalog URLs in DB:")
    for url in homepage_urls:
        print(url)

if __name__ == "__main__":
    asyncio.run(main())
