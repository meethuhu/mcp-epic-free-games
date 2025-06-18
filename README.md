# MCP Epic Free Games

A Model Context Protocol (MCP) server that provides access to Epic Games Store free games information.

## Installation

```bash
pip install mcp-epic-free-games
```

## Usage

Add the following to your MCP client configuration:

```json
{
  "mcpServers": {
    "epic-free-games": {
      "type": "stdio",
      "description": "Get free game information from Epic Games Store.",
      "command": "uvx",
      "args": [
        "mcp-epic-free-games"
      ],
      "env": {
        "TIME_ZONE": "Asia/Shanghai"
      }
    }
  }
}
```

## Features

This server provides tools to get information about free games on the Epic Games Store.

### `get_now_free_games`

Get information about currently free games.

**Returns:** Game title, description, cover image, claim URL, and free period dates.

### `get_upcoming_free_games`

Get information about upcoming free games.

**Returns:** Game title, description, cover image, claim URL, and free period dates.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.