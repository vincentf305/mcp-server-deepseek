import pytest
from unittest.mock import MagicMock, patch
import docker
from mcp import Request, Response, Message, Function
from mcp_server.server import DeepseekServer, DeepseekClient

@pytest.fixture
def server():
    server = DeepseekServer()
    # Mock the DeepseekClient
    server.deepseek_client = MagicMock()
    server.deepseek_client.generate_response.return_value = "Test response"
    return server

@pytest.mark.asyncio
async def test_handle_chat_request(server):
    # Create a test request
    request = Request(
        function="chat",
        messages=[
            Message(role="user", content="Hello")
        ],
        parameters={"temperature": 0.7}
    )

    # Test handling chat request
    response = await server.handle_request(request)

    # Verify response
    assert isinstance(response, Response)
    assert response.error is None
    assert response.message.role == "assistant"
    assert response.message.content == "Test response"
    
    # Verify the client was called with correct parameters
    server.deepseek_client.generate_response.assert_called_once()
    call_args = server.deepseek_client.generate_response.call_args
    assert call_args[1]["temperature"] == 0.7

@pytest.mark.asyncio
async def test_handle_invalid_function(server):
    # Test with invalid function name
    request = Request(
        function="invalid_function",
        messages=[
            Message(role="user", content="Hello")
        ]
    )

    response = await server.handle_request(request)
    assert isinstance(response, Response)
    assert response.error is not None
    assert "Unknown function" in response.error

@pytest.mark.asyncio
async def test_handle_chat_error(server):
    # Make the client raise an exception
    server.deepseek_client.generate_response.side_effect = Exception("Test error")

    request = Request(
        function="chat",
        messages=[
            Message(role="user", content="Hello")
        ]
    )

    response = await server.handle_request(request)
    assert isinstance(response, Response)
    assert response.error is not None
    assert "Test error" in response.error

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
            response = await client.generate_response(
                [Message(role="user", content="Hello")],
                temperature=0.7
            )
            assert response == "Test response"

@pytest.mark.asyncio
async def test_deepseek_client_container_not_found():
    with patch('docker.from_env') as mock_docker:
        # Mock container not found
        mock_docker.return_value.containers.get.side_effect = docker.errors.NotFound("Container not found")
        
        with pytest.raises(docker.errors.NotFound):
            client = DeepseekClient()

@pytest.mark.asyncio
async def test_deepseek_client_api_error():
    with patch('docker.from_env') as mock_docker:
        # Mock container
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_docker.return_value.containers.get.return_value = mock_container
        
        client = DeepseekClient()
        
        # Mock API error
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 500
            mock_response.__aenter__.return_value = mock_response
            mock_response.text.return_value = "Internal Server Error"
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await client.generate_response(
                    [Message(role="user", content="Hello")]
                )
            assert "Error from Deepseek API" in str(exc_info.value)

@pytest.mark.asyncio
async def test_server_registered_functions(server):
    # Test that the chat function is properly registered
    assert "chat" in server.functions
    chat_function = server.functions["chat"]
    assert isinstance(chat_function, Function)
    
    # Verify function parameters
    params = chat_function.parameters
    assert "temperature" in params
    assert params["temperature"]["type"] == "number"
    assert params["temperature"]["minimum"] == 0.0
    assert params["temperature"]["maximum"] == 2.0
    
    assert "max_tokens" in params
    assert params["max_tokens"]["type"] == "integer"
    assert params["max_tokens"]["optional"] is True

if __name__ == "__main__":
    pytest.main(["-v"])