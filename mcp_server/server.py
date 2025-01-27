import asyncio
import logging
from typing import List, Optional
import docker
import aiohttp
from mcp import Server, Request, Response, Message, Function, FunctionCall

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    async def generate_response(self, messages: List[Message], temperature: float = 0.7) -> str:
        """Generate a response from the Deepseek model."""
        try:
            messages_dict = [msg.dict() for msg in messages]
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/v1/chat/completions",
                    json={
                        "messages": messages_dict,
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

class DeepseekServer(Server):
    def __init__(self):
        super().__init__()
        self.deepseek_client = DeepseekClient()
        
        # Register the chat completion function
        self.register_function(
            Function(
                name="chat",
                description="Generate a response using the Deepseek model",
                parameters={
                    "temperature": {
                        "type": "number",
                        "description": "Controls randomness in the response",
                        "default": 0.7,
                        "minimum": 0.0,
                        "maximum": 2.0
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum number of tokens to generate",
                        "optional": True
                    }
                }
            )
        )

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming MCP requests."""
        try:
            if request.function == "chat":
                return await self._handle_chat(request)
            else:
                raise ValueError(f"Unknown function: {request.function}")
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return Response(error=str(e))

    async def _handle_chat(self, request: Request) -> Response:
        """Handle chat completion requests."""
        try:
            temperature = request.parameters.get("temperature", 0.7)
            
            response_text = await self.deepseek_client.generate_response(
                request.messages,
                temperature=temperature
            )
            
            return Response(message=Message(
                role="assistant",
                content=response_text
            ))
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return Response(error=str(e))

def main():
    server = DeepseekServer()
    asyncio.run(server.serve("0.0.0.0", 8765))

if __name__ == "__main__":
    main()