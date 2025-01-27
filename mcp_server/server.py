import asyncio
import click
import json
import logging
import requests
import sys

import mcp
import mcp.types as types

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

from .config import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def serve() -> Server:
    server = Server("deepseek-server")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="chat",
                description="Generate responses using the Deepseek model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            }
                        },
                        "model": {"type": "string", "default": "deepseek-coder", "enum": ["deepseek-coder", "deepseek-chat"]},
                        "temperature": {"type": "number", "default": 0.7, "minimum": 0, "maximum": 2},
                        "max_tokens": {"type": "integer", "default": 500, "minimum": 1, "maximum": 4000},
                        "top_p": {"type": "number", "default": 1.0, "minimum": 0, "maximum": 1},
                        "stream": {"type": "boolean", "default": False}
                    },
                    "required": ["messages"]
                }
            )
        ]

    @server.call_tool()
    async def handle_tool_call(name: str, arguments: dict | None) -> list[types.TextContent]:
        try:
            if not arguments:
                raise ValueError("No arguments provided")

            if name == "chat":
                messages = arguments["messages"]
                model = arguments.get("model", "deepseek-coder")
                temperature = arguments.get("temperature", 0.7)
                max_tokens = arguments.get("max_tokens", 500)
                top_p = arguments.get("top_p", 1.0)
                stream = arguments.get("stream", False)

                deepseek_request = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "stream": stream
                }

                json_data = json.dumps(deepseek_request)

                response = requests.post(
                    f"{settings.deepseek_base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    data=json_data
                )

                response.raise_for_status()
                data = response.json()
                chat_response = data["choices"][0]["message"]["content"]
                
                return [types.TextContent(type="text", text=chat_response)]

            raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Tool call failed: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

@click.command()
def main():
    try:
        async def _run():
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                server = serve()
                await server.run(
                    read_stream, write_stream,
                    InitializationOptions(
                        server_name="deepseek-server",
                        server_version="0.1.0",
                        capabilities=server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Server failed")
        sys.exit(1)

if __name__ == "__main__":
    main()