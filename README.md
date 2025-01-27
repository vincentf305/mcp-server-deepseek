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

## Setup Environment Variables

Create a `.env` file in the root directory of the project and add the following environment variable:

```
DEEPSEEK_API_KEY=your_api_key_here
```

Make sure to replace `your_api_key_here` with your actual Deepseek API key.

## Running the Server

### Using Docker

1. Build the Docker image:

```bash
docker build -t mcp_server_deepseek .
```

2. Run the container:

```bash
docker run -d \
  --name mcp-server-deepseek \
  -p 8765:8765 \
  -e DEEPSEEK_API_KEY=your_api_key_here \
  mcp-server-deepseek
```

### Running Locally

```bash
python -m mcp_server_deepseek.server
```

## Usage with Claude Desktop

1. Ensure you have a Deepseek API key

2. Add the following to your Claude Desktop configuration (claude_desktop_config.json):

```json
{
  "mcpServers": {
    "deepseek-server": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "DEEPSEEK_API_KEY",
        "mcp_server_deepseek"
      ],
      "env": {
        "DEEPSEEK_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

3. Restart Claude Desktop to load the new configuration

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## License

MIT License - see the [LICENSE](LICENSE) file for details
