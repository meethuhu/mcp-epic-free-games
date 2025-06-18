# MCP Epic Free Games

A Model Context Protocol (MCP) server that provides access to Epic Games Store free games information.

## Features

- Get currently free games from Epic Games Store
- Get upcoming free games information
- Cached responses for better performance
- Easy integration with MCP-compatible clients

## Installation

### From PyPI

```bash
pip install mcp-epic-free-games
```

### From Source

```bash
git clone https://github.com/meethuhu/mcp-epic-free-games.git
cd mcp-epic-free-games
pip install -e .
```

## Usage

### As a standalone MCP server

```bash
mcp-epic-free-games
```

### In your MCP client configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "epic-free-games": {
      "command": "mcp-epic-free-games"
    }
  }
}
```

## Available Tools

### get_now_free_games

Get information about currently free games from Epic Games Store.

**Returns:**
- Game title
- Game description
- Game cover image
- Claim URL
- Free period dates

### get_upcoming_free_games

Get information about upcoming free games from Epic Games Store.

**Returns:**
- Game title
- Game description  
- Game cover image
- Claim URL
- Free period dates

## Development

### Requirements

- Python 3.13+
- httpx
- mcp

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/mcp-epic-free-games.git
cd mcp-epic-free-games
pip install -e .
```

### Running Tests

```bash
pytest
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.