from .server import serve


def main():
    """Get free game information from Epic Games Store. MCP server"""
    import asyncio

    asyncio.run(serve())


if __name__ == "__main__":
    main()
