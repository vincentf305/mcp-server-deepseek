# MCP Server for Deepseek Integration

This repository contains a Model Control Protocol (MCP) server implementation that allows Claude Desktop to use Deepseek models running in Docker.

## Prerequisites

- Docker
- Python 3.11 or later
- A running Deepseek model container

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vincentf305/mcp-server-deepseek.git
cd mcp-server-deepseek
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

### Using Docker

1. Build the Docker image:
```bash
docker build -t mcp-server-deepseek .
```

2. Run the container:
```bash
docker run -d \
  --name mcp-server \
  -p 8765:8765 \
  --network host \
  mcp-server-deepseek
```

Note: The `--network host` flag is required to allow the MCP server to communicate with the Deepseek model container.

### Running Locally

```bash
python -m mcp_server.server
```

## Testing

Run the tests using pytest:

```bash
pytest tests/
```

For coverage report:

```bash
pytest --cov=mcp_server tests/
```

## Usage with Claude Desktop

1. Ensure you have the Deepseek model running in a Docker container named `deepseek-coder`
2. Start the MCP server
3. Configure Claude Desktop to connect to `ws://localhost:8765`

## API

The server implements the MCP protocol over WebSocket. Messages should be in the following format:

### Chat Request
```json
{
    "type": "chat",
    "payload": {
        "messages": [
            {
                "role": "user",
                "content": "Your message here"
            }
        ],
        "temperature": 0.7
    }
}
```

### Chat Response
```json
{
    "type": "chat_response",
    "payload": {
        "role": "assistant",
        "content": "Response from Deepseek model"
    },
    "status": "success"
}
```

## Error Handling

The server will return error messages in the following format:

```json
{
    "type": "error",
    "message": "Error description"
}
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## License

MIT License - see the [LICENSE](LICENSE) file for details