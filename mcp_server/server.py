import asyncio
import json
import logging
from typing import Dict, Optional
import docker
import aiohttp
from pydantic import BaseModel, Field
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str = Field(..., regex="^(user|assistant|system)$")
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)

class DeepseekClient:
    def __init__(self, container_name: str = "deepseek-coder"):
        self.docker_client = docker.from_env()
        self.container_name = container_name
        self._ensure_container_running()

    def _ensure_container_running(self):
        """Ensure the Deepseek container is running."""
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status != "running":
                container.start()
        except docker.errors.NotFound:
            logger.error(f"Container {self.container_name} not found")
            raise

    async def generate_response(self, messages: list[dict], temperature: float = 0.7) -> str:
        """Generate a response from the Deepseek model."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/v1/chat/completions",
                    json={
                        "messages": messages,
                        "temperature": temperature,
                        "model": "deepseek-coder"
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Error from Deepseek API: {await response.text()}")
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

class MCPServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.deepseek_client = DeepseekClient()

    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Handle incoming WebSocket connections."""
        client_id = str(id(websocket))
        self.connections[client_id] = websocket
        logger.info(f"New connection established: {client_id}")

        try:
            async for message in websocket:
                try:
                    await self.handle_message(websocket, message)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self.send_error(websocket, str(e))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {client_id}")
        finally:
            del self.connections[client_id]

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming messages from clients."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "chat":
                request = ChatRequest(**data["payload"])
                await self.handle_chat_message(websocket, request)
            else:
                await self.send_error(websocket, f"Unknown message type: {message_type}")
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON message")
        except Exception as e:
            await self.send_error(websocket, str(e))

    async def handle_chat_message(self, websocket: WebSocketServerProtocol, request: ChatRequest):
        """Handle chat messages and interact with Deepseek model."""
        try:
            messages = [msg.dict() for msg in request.messages]
            response_text = await self.deepseek_client.generate_response(
                messages,
                temperature=request.temperature
            )
            
            response = {
                "type": "chat_response",
                "payload": {
                    "role": "assistant",
                    "content": response_text
                },
                "status": "success"
            }
            await websocket.send(json.dumps(response))
        except Exception as e:
            await self.send_error(websocket, str(e))

    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """Send error message to client."""
        error_response = {
            "type": "error",
            "message": error_message
        }
        await websocket.send(json.dumps(error_response))

    async def start(self):
        """Start the WebSocket server."""
        async with websockets.serve(self.handle_connection, self.host, self.port):
            logger.info(f"MCP Server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

def main():
    server = MCPServer()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()