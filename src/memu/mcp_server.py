"""MCP (Model Context Protocol) Server for MemU.

This server exposes MemU's memory management capabilities as MCP tools,
resources, and prompts, making it compatible with MCP clients like Claude Desktop,
Cursor, and other AI agents.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Import fastmcp for MCP server functionality
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Resource, TextContent, Tool
except ImportError:
    print("Error: mcp package not installed. Please run: pip install mcp", file=sys.stderr)
    sys.exit(1)

from memu.app import MemoryService

logger = logging.getLogger(__name__)


class MemUMCPServer:
    """MCP Server wrapper for MemU memory service."""

    def __init__(self, config_path: str | None = None):
        """Initialize the MCP server with optional configuration."""
        self.config = self._load_config(config_path)
        self.service: MemoryService | None = None
        self.server = Server("memu-server")

        # Register handlers
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load configuration from file or environment."""
        config: dict[str, Any] = {
            "provider": os.getenv("MEMU_PROVIDER", "openai"),
            "llm_profiles": {},
            "database_config": {},
            "retrieve_config": {},
        }

        # Load from config file if provided
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                file_config = json.load(f)
                config.update(file_config)

        # Build llm_profiles from environment or config
        provider = config.get("provider", "openai")

        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            model = os.getenv("OLLAMA_MODEL", "llama3")
            config["llm_profiles"] = {
                "default": {
                    "base_url": base_url,
                    "api_key": os.getenv("OLLAMA_API_KEY", "ollama"),
                    "chat_model": model,
                    "embed_model": model,
                    "client_backend": "sdk",
                }
            }
        elif provider == "openrouter":
            config["llm_profiles"] = {
                "default": {
                    "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
                    "chat_model": os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
                    "client_backend": "sdk",
                }
            }
        elif provider == "deepinfra":
            config["llm_profiles"] = {
                "default": {
                    "base_url": os.getenv("DEEPINFRA_BASE_URL", "https://api.deepinfra.com/v1/openai"),
                    "api_key": os.getenv("DEEPINFRA_API_KEY", ""),
                    "chat_model": os.getenv("DEEPINFRA_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct"),
                    "client_backend": "sdk",
                }
            }
        elif provider == "fireworks":
            config["llm_profiles"] = {
                "default": {
                    "base_url": os.getenv("FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1"),
                    "api_key": os.getenv("FIREWORKS_API_KEY", ""),
                    "chat_model": os.getenv("FIREWORKS_MODEL", "accounts/fireworks/models/llama-v3p1-70b-instruct"),
                    "client_backend": "sdk",
                }
            }
        elif provider == "lmstudio":
            config["llm_profiles"] = {
                "default": {
                    "base_url": os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
                    "api_key": os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
                    "chat_model": os.getenv("LMSTUDIO_MODEL", "local-model"),
                    "client_backend": "sdk",
                }
            }
        else:  # default to openai or custom
            config["llm_profiles"] = {
                "default": {
                    "base_url": os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
                    "api_key": os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
                    "chat_model": os.getenv("LLM_CHAT_MODEL", "gpt-4o-mini"),
                    "embed_model": os.getenv("LLM_EMBED_MODEL", "text-embedding-3-small"),
                    "client_backend": "sdk",
                }
            }

        # Database configuration
        config["database_config"] = {
            "metadata_store": {
                "provider": os.getenv("DB_PROVIDER", "inmemory"),
                "dsn": os.getenv("DB_DSN"),
            }
        }

        # Retrieve configuration
        config["retrieve_config"] = {
            "method": os.getenv("RETRIEVE_METHOD", "rag"),
        }

        return config

    async def _init_service(self) -> None:
        """Initialize the MemU service."""
        if self.service is None:
            self.service = MemoryService(
                llm_profiles=self.config["llm_profiles"],
                database_config=self.config["database_config"],
                retrieve_config=self.config["retrieve_config"],
            )

    def _register_tools(self) -> None:
        """Register MCP tools for MemU operations."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools."""
            return [
                Tool(
                    name="memorize",
                    description="Process and extract structured memory from input resources (conversations, documents, images, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "resource_url": {
                                "type": "string",
                                "description": "File path or URL to the resource",
                            },
                            "modality": {
                                "type": "string",
                                "enum": ["conversation", "document", "image", "video", "audio"],
                                "description": "Type of content to process",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID to scope the memory to (optional)",
                            },
                        },
                        "required": ["resource_url", "modality"],
                    },
                ),
                Tool(
                    name="retrieve",
                    description="Query and retrieve relevant memories based on text queries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant memories",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID to filter memories (optional)",
                            },
                            "method": {
                                "type": "string",
                                "enum": ["rag", "llm"],
                                "description": "Retrieval method: 'rag' for fast embedding search, 'llm' for deep semantic understanding",
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="list_categories",
                    description="List all memory categories with their summaries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID to filter categories (optional)",
                            },
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            await self._init_service()

            if name == "memorize":
                result = await self._handle_memorize(arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "retrieve":
                result = await self._handle_retrieve(arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "list_categories":
                result = await self._handle_list_categories(arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            else:
                raise ValueError(f"Unknown tool: {name}")

    def _register_resources(self) -> None:
        """Register MCP resources for accessing memory data."""

        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="memory://categories",
                    name="Memory Categories",
                    description="All memory categories with their descriptions",
                    mimeType="application/json",
                ),
                Resource(
                    uri="memory://stats",
                    name="Memory Statistics",
                    description="Statistics about stored memories",
                    mimeType="application/json",
                ),
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource by URI."""
            await self._init_service()

            if uri == "memory://categories":
                categories = await self._get_categories()
                return json.dumps(categories, indent=2)

            elif uri == "memory://stats":
                stats = await self._get_stats()
                return json.dumps(stats, indent=2)

            else:
                raise ValueError(f"Unknown resource: {uri}")

    def _register_prompts(self) -> None:
        """Register MCP prompts for common memory operations."""

        @self.server.list_prompts()
        async def list_prompts() -> list[dict[str, Any]]:
            """List available prompts."""
            return [
                {
                    "name": "analyze_conversation",
                    "description": "Analyze a conversation and extract structured memory",
                    "arguments": [
                        {
                            "name": "conversation_file",
                            "description": "Path to the conversation JSON file",
                            "required": True,
                        }
                    ],
                },
                {
                    "name": "search_memories",
                    "description": "Search through stored memories with a natural language query",
                    "arguments": [
                        {"name": "query", "description": "What to search for", "required": True},
                        {"name": "user_id", "description": "User ID to filter by", "required": False},
                    ],
                },
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> dict[str, Any]:
            """Get a specific prompt."""
            arguments = arguments or {}

            if name == "analyze_conversation":
                conversation_file = arguments.get("conversation_file", "")
                return {
                    "description": "Analyze and extract memories from a conversation",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": f"Please analyze the conversation in {conversation_file} and extract structured memory from it.",
                            },
                        }
                    ],
                }

            elif name == "search_memories":
                query = arguments.get("query", "")
                return {
                    "description": "Search stored memories",
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": f"Search my memories for: {query}"},
                        }
                    ],
                }

            else:
                raise ValueError(f"Unknown prompt: {name}")

    async def _handle_memorize(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle memorize tool call."""
        resource_url = arguments.get("resource_url")
        modality = arguments.get("modality")
        user_id = arguments.get("user_id")

        user_data = {"user_id": user_id} if user_id else None

        assert self.service is not None
        result = await self.service.memorize(
            resource_url=resource_url,
            modality=modality,
            user=user_data,
        )

        # Simplify result for better readability
        return {
            "status": "success",
            "resource": result.get("resource", {}).get("url"),
            "items_extracted": len(result.get("items", [])),
            "categories_updated": len(result.get("categories", [])),
            "categories": [
                {"name": cat.get("name"), "summary": cat.get("summary", "")[:200]}
                for cat in result.get("categories", [])
            ],
        }

    async def _handle_retrieve(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle retrieve tool call."""
        query = arguments.get("query", "")
        user_id = arguments.get("user_id")
        method = arguments.get("method")

        queries = [{"role": "user", "content": {"text": query}}]
        where = {"user_id": user_id} if user_id else None

        assert self.service is not None
        if method:
            original_method = self.service.retrieve_config.method
            self.service.retrieve_config.method = method

        result = await self.service.retrieve(queries=queries, where=where)

        if method:
            self.service.retrieve_config.method = original_method

        # Simplify result
        return {
            "query": query,
            "categories": [
                {"name": cat.get("name"), "summary": cat.get("summary", cat.get("description", ""))[:200]}
                for cat in result.get("categories", [])
            ],
            "items": [
                {
                    "type": item.get("memory_type"),
                    "summary": item.get("summary", "")[:200],
                }
                for item in result.get("items", [])
            ],
            "resources": [res.get("url") for res in result.get("resources", [])],
        }

    async def _handle_list_categories(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle list_categories tool call."""
        user_id = arguments.get("user_id")
        where = {"user_id": user_id} if user_id else None

        assert self.service is not None
        categories = await self.service.list_categories(where=where)

        return {
            "categories": [
                {
                    "name": cat.get("name"),
                    "description": cat.get("description", ""),
                    "summary": cat.get("summary", "")[:200] if cat.get("summary") else "",
                }
                for cat in categories
            ]
        }

    async def _get_categories(self) -> dict[str, Any]:
        """Get all categories."""
        assert self.service is not None
        categories = await self.service.list_categories()
        return {"categories": categories}

    async def _get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        # This is a placeholder - implement based on available service methods
        return {
            "status": "operational",
            "provider": self.config.get("provider"),
        }

    async def run(self) -> None:
        """Run the MCP server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


async def main() -> None:
    """Main entry point for the MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],  # Log to stderr to not interfere with stdio
    )

    # Get config path from environment or use default
    config_path = os.getenv("MEMU_CONFIG_PATH")

    # Create and run server
    server = MemUMCPServer(config_path=config_path)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
