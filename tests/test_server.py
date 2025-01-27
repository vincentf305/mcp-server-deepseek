import json
import pytest
import websockets
import asyncio
from unittest.mock import MagicMock, patch
from mcp_server.server import MCPServer, ChatRequest, ChatMessage, DeepseekClient

@pytest.fixture
async def server():
    server = MCPServer(host="localhost", port=8765)
    # Mock the DeepseekClient
    server.deepseek_client = MagicMock()
    server.deepseek_client.generate_response.return_value = "Test response"
    return server

@pytest.fixture
async def websocket():
    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
            self.closed = False

        async def send(self, message):
            self.sent_messages.append(message)

        async def close(self):
            self.closed = True

    return MockWebSocket()

@pytest.mark.asyncio
async def test_handle_chat_message(server, websocket):
    # Test data
    chat_request = ChatRequest(
        messages=[
            ChatMessage(role="user", content="Hello")
        ],
        temperature=0.7
    )

    # Test handling chat message
    await server.handle_chat_message(websocket, chat_request)

    # Verify response
    assert len(websocket.sent_messages) == 1
    response = json.loads(websocket.sent_messages[0])
    assert response["type"] == "chat_response"
    assert response["status"] == "success"
    assert response["payload"]["role"] == "assistant"
    assert response["payload"]["content"] == "Test response"

@pytest.mark.asyncio
async def test_handle_invalid_message(server, websocket):
    # Test invalid JSON
    await server.handle_message(websocket, "invalid json")

    # Verify error response
    assert len(websocket.sent_messages) == 1
    response = json.loads(websocket.sent_messages[0])
    assert response["type"] == "error"
    assert "Invalid JSON message" in response["message"]

@pytest.mark.asyncio
async def test_handle_unknown_message_type(server, websocket):
    # Test unknown message type
    message = json.dumps({"type": "unknown", "payload": {}})
    await server.handle_message(websocket, message)

    # Verify error response
    assert len(websocket.sent_messages) == 1
    response = json.loads(websocket.sent_messages[0])
    assert response["type"] == "error"
    assert "Unknown message type" in response["message"]

@pytest.mark.asyncio
async def test_deepseek_client():
    with patch('docker.from_env') as mock_docker:
        # Mock container
        mock_container = MagicMock()
        mock_container.status = "running"
        
        # Mock docker client
        mock_docker.return_value.containers.get.return_value = mock_container
        
        client = DeepseekClient()
        
        # Test container check
        assert mock_docker.return_value.containers.get.called
        
        # Mock aiohttp response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.__aenter__.return_value = mock_response
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            mock_post.return_value = mock_response
            
            # Test generate response
            messages = [{"role": "user", "content": "Hello"}]
            response = await client.generate_response(messages)
            assert response == "Test response"

@pytest.mark.asyncio
async def test_deepseek_client_error_handling():
    with patch('docker.from_env') as mock_docker:
        # Mock container not found
        mock_docker.return_value.containers.get.side_effect = docker.errors.NotFound("Container not found")
        
        with pytest.raises(docker.errors.NotFound):
            client = DeepseekClient()

@pytest.mark.asyncio
async def test_server_connection_handling(server):
    # Test connection handling
    test_websocket = MagicMock()
    test_websocket.__aiter__.return_value = [
        json.dumps({
            "type": "chat",
            "payload": {
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.7
            }
        })
    ]

    await server.handle_connection(test_websocket)
    
    # Verify that the connection was handled and message was processed
    assert len(server.connections) == 0  # Connection should be removed after handling

@pytest.mark.asyncio
async def test_server_error_handling(server, websocket):
    # Test server error handling with invalid message format
    invalid_request = ChatRequest(
        messages=[
            ChatMessage(role="invalid_role", content="Hello")  # This should trigger a validation error
        ]
    )
    
    with pytest.raises(Exception):
        await server.handle_chat_message(websocket, invalid_request)

if __name__ == "__main__":
    pytest.main(["-v"])