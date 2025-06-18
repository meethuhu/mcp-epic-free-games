import os
from datetime import datetime, timedelta
from enum import Enum
import json
from typing import Sequence
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from pydantic import BaseModel

TIME_ZONE = os.getenv('TIME_ZONE', 'CST')


class EpicTools(str, Enum):
    GET_NOW_FREE_GAMES = "get_now_free_games"
    GET_UPCOMING_FREE_GAMES = "get_upcoming_free_games"


class GameInfo(BaseModel):
    title: str
    description: str | None = None
    cover: str | None = None
    get_url: str | None = None
    free_start_date: str | None = None
    free_end_date: str | None = None


class EpicGamesResult(BaseModel):
    games: list[GameInfo]
    count: int
    last_updated: str


class EpicGamesServer:
    def __init__(self):
        self.base_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        self._cache = None
        self._cache_time = None
        self._cache_expiry = timedelta(minutes=10)  # Cache for 10 minutes

    async def get_epic_games_store_info(self) -> dict | None:
        """Get the original information from the Epic Games Store."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise ValueError(f"Failed to fetch Epic Games data: {str(e)}")
        except Exception as e:
            raise ValueError(f"An error occurred: {str(e)}")

    def _extract_game_details(self, item: dict) -> dict:
        """Helper function to extract common game details."""
        title = item.get("title")
        description = item.get("description")

        product_slug = None
        if item.get("offerMappings"):
            product_slug = item["offerMappings"][0].get("pageSlug")
        if not product_slug and item.get("catalogNs", {}).get("mappings"):
            product_slug = item["catalogNs"]["mappings"][0].get("pageSlug")

        get_url = f"https://store.epicgames.com/zh-CN/p/{product_slug}" if product_slug else None

        cover_image_url = ""
        key_images = item.get("keyImages", [])
        for img in key_images:
            if img.get("type") == "OfferImageWide":
                cover_image_url = img.get("url")
                break
        if not cover_image_url and key_images:
            img_candidate = key_images[0]
            if isinstance(img_candidate, dict):
                cover_image_url = img_candidate.get("url", "")

        return {
            "title": title,
            "description": description,
            "cover": cover_image_url,
            "get_url": get_url,
        }

    def _is_game(self, item: dict) -> bool:
        """Determine if the item is a game based on its offer type and categories."""
        if not isinstance(item, dict):
            return False
        offer_type = item.get("offerType")
        if offer_type == "BASE_GAME":
            return True
        elif offer_type == "OTHERS":
            categories = item.get("categories", [])
            category_paths = [cat.get("path")
                              for cat in categories if cat.get("path")]
            return "games" in category_paths and "bundles" not in category_paths and "addons" not in category_paths
        return False

    def _extract_now_free(self, promotions: dict, game_details: dict) -> list[dict]:
        """Extract the list of currently free games from promotions."""
        free_list = []
        groups = promotions.get("promotionalOffers")
        if groups and isinstance(groups, list):
            for group in groups:
                for offer in group.get("promotionalOffers", []):
                    free_list.append(
                        {
                            **game_details,
                            "free_start_date": offer.get("startDate"),
                            "free_end_date": offer.get("endDate"),
                        }
                    )
        return free_list

    async def _get_and_process_games(self) -> tuple[list[dict], list[dict]]:
        """Fetch and process games from Epic Games Store to get now free and upcoming free games."""
        now = datetime.now()
        if self._cache and self._cache_time and (now - self._cache_time < self._cache_expiry):
            return self._cache

        data = await self.get_epic_games_store_info()
        if not data or "data" not in data:
            return [], []

        elements = data["data"].get("Catalog", {}).get(
            "searchStore", {}).get("elements", [])

        now_free_details = []
        upcoming_free_details = []

        for item in elements:
            if not self._is_game(item):
                continue

            game_details = self._extract_game_details(item)
            promotions = item.get("promotions") or {}

            now_free_details.extend(
                self._extract_now_free(promotions, game_details))

            # Extract upcoming free games
            groups = promotions.get("upcomingPromotionalOffers")
            if groups and isinstance(groups, list):
                for group in groups:
                    for offer in group.get("promotionalOffers", []):
                        upcoming_free_details.append(
                            {
                                **game_details,
                                "free_start_date": offer.get("startDate"),
                                "free_end_date": offer.get("endDate"),
                            }
                        )

        now_free_titles = {game["title"] for game in now_free_details}

        final_upcoming_free = [
            game for game in upcoming_free_details if game["title"] not in now_free_titles
        ]

        self._cache = (now_free_details, final_upcoming_free)
        self._cache_time = now
        return self._cache

    async def get_now_free_games(self) -> EpicGamesResult:
        """Return list of currently free games."""
        now_free, _ = await self._get_and_process_games()

        games = [GameInfo(**game) for game in now_free]
        return EpicGamesResult(
            games=games,
            count=len(games),
            last_updated=datetime.now().isoformat()
        )

    async def get_upcoming_free_games(self) -> EpicGamesResult:
        """Return list of upcoming free games, excluding current free ones."""
        _, upcoming_free = await self._get_and_process_games()

        games = [GameInfo(**game) for game in upcoming_free]
        return EpicGamesResult(
            games=games,
            count=len(games),
            last_updated=datetime.now().isoformat()
        )


async def serve() -> None:
    """Main MCP server function."""
    server = Server("mcp-epic-free-games-info")
    epic_server = EpicGamesServer()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available Epic Games tools."""
        return [
            Tool(
                name=EpicTools.GET_NOW_FREE_GAMES.value,
                description="Get currently free games from Epic Games Store",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name=EpicTools.GET_UPCOMING_FREE_GAMES.value,
                description="Get upcoming free games from Epic Games Store",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls for Epic Games queries."""
        try:
            result: EpicGamesResult
            prompt = ""
            match name:
                case EpicTools.GET_NOW_FREE_GAMES.value:
                    result = await epic_server.get_now_free_games()
                    prompt = f"You are an Epic Games assistant, and the user wants to know about currently free games. Please provide the game title, game cover (in image format), game description, claim link, and claim period (to {TIME_ZONE}) in a clear structure and Markdown format. Here is the complete JSON:"

                case EpicTools.GET_UPCOMING_FREE_GAMES.value:
                    result = await epic_server.get_upcoming_free_games()
                    prompt = f"You are an Epic Games assistant, and the user wants to know about upcoming free games. Please provide the game title, game cover (in image format), game description, claim link, and claim period (to {TIME_ZONE}) in a clear structure and Markdown format. Here is the complete JSON:"

                case _:
                    raise ValueError(f"Unknown tool: {name}")

            json_data = json.dumps(result.model_dump(), indent=2)
            output_text = f"{prompt}\n\n```json\n{json_data}\n```"

            return [
                TextContent(type="text", text=output_text)
            ]

        except Exception as e:
            raise ValueError(
                f"Error processing mcp-epic-free-games query: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
