# MCP Server for Deepseek Integration

This repository contains a Model Control Protocol (MCP) server implementation that allows Claude Desktop to use Deepseek models running in Docker.

## Prerequisites

- Docker
- Python 3.11 or later
- A Deepseek API key
- Claude Desktop

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
  -e DEEPSEEK_API_KEY=your_api_key_here \
  mcp-server-deepseek
```

### Running Locally

```bash
export DEEPSEEK_API_KEY=your_api_key_here
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

1. Ensure you have a Deepseek API key
2. Create a `.env` file with your API key:
```bash
DEEPSEEK_API_KEY=your_api_key_here
```

3. Add the following to your Claude Desktop configuration (claude_desktop_config.json):
```json
{
  "tools": [
    {
      "name": "Deepseek Tools",
      "type": "mcp",
      "config": {
        "command": ["docker", "run", "--rm", "-i", 
          "-e", "DEEPSEEK_API_KEY=your_api_key_here",
          "mcp-server-deepseek"
        ]
      }
    }
  ]
}
```

4. Restart Claude Desktop to load the new configuration

## API

The server implements the MCP protocol and provides the following tool:

### Chat Tool
This tool allows you to interact with Deepseek models for code and text generation.

Parameters:
- messages (required): Array of message objects with role and content
- model (optional): "deepseek-coder" or "deepseek-chat" (default: "deepseek-coder")
- temperature (optional): Controls randomness (0-2, default: 0.7)
- max_tokens (optional): Maximum tokens to generate (1-4000, default: 500)
- top_p (optional): Nucleus sampling parameter (0-1, default: 1.0)
- stream (optional): Enable streaming responses (default: false)

Example Usage:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Write a Python function to sort a list"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500
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