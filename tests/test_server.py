import json
import pytest
from unittest.mock import patch, MagicMock
import mcp.types as types
from mcp_server.server import serve
from mcp.server import Request

@pytest.fixture
def server():
    return serve()

@pytest.mark.asyncio
async def test_list_tools():
    # Create a test request
    with patch('requests.post') as mock_post:
        tools = await serve().list_tools()
        
        assert len(tools) == 1
        chat_tool = tools[0]
        assert chat_tool.name == "chat"
        assert isinstance(chat_tool, types.Tool)
        
        # Verify schema
        schema = chat_tool.inputSchema
        assert schema["type"] == "object"
        assert "messages" in schema["properties"]
        assert "temperature" in schema["properties"]
        assert "max_tokens" in schema["properties"]
        assert "model" in schema["properties"]

@pytest.mark.asyncio
async def test_chat_call():
    test_messages = [{"role": "user", "content": "Hello"}]
    
    with patch('requests.post') as mock_post:
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        request = Request(
            name="chat",
            arguments={
                "messages": test_messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
        )

        result = await serve().call_tool(request)

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].text == "Test response"

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "v1/chat/completions" in call_args[0][0]
        
        sent_data = json.loads(call_args[1]["data"])
        assert sent_data["messages"] == test_messages
        assert sent_data["temperature"] == 0.7
        assert sent_data["max_tokens"] == 500

@pytest.mark.asyncio
async def test_chat_call_error():
    with patch('requests.post') as mock_post:
        # Mock API error
        mock_post.side_effect = Exception("API Error")

        request = Request(
            name="chat",
            arguments={
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )

        result = await serve().call_tool(request)

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Error:" in result[0].text
        assert "API Error" in result[0].text

@pytest.mark.asyncio
async def test_unknown_tool():
    request = Request(
        name="unknown_tool",
        arguments={}
    )
    
    result = await serve().call_tool(request)
    
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert "Error:" in result[0].text
    assert "Unknown tool" in result[0].text

@pytest.mark.asyncio
async def test_missing_arguments():
    request = Request(
        name="chat",
        arguments=None
    )
    
    result = await serve().call_tool(request)
    
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert "Error:" in result[0].text
    assert "No arguments provided" in result[0].text

@pytest.mark.asyncio
async def test_api_error_response():
    with patch('requests.post') as mock_post:
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response

        request = Request(
            name="chat",
            arguments={
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )

        result = await serve().call_tool(request)

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Error:" in result[0].text
        assert "Bad Request" in result[0].text

if __name__ == "__main__":
    pytest.main(["-v"])