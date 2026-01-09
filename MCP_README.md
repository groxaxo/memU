# MemU MCP Server

The MemU MCP (Model Context Protocol) Server enables you to use MemU's memory management capabilities as a plugin in MCP-compatible clients like Claude Desktop, Cursor, and other AI agents.

## 🎯 What is MCP?

The [Model Context Protocol](https://modelcontextprotocol.io) is an open standard that allows AI applications to connect to external tools and data sources. By running MemU as an MCP server, you can give any MCP client access to persistent, intelligent memory management.

## 🚀 Features

- **Universal OpenAI-Compatible Support**: Works with any OpenAI-compatible API endpoint
- **Local & Cloud**: Seamlessly switch between local models (Ollama, LMStudio) and cloud providers
- **MCP Tools**: Expose core MemU functions as callable tools
- **MCP Resources**: Access memory data as structured resources
- **MCP Prompts**: Pre-packaged prompts for common operations
- **Docker-First**: Fully containerized with automated installation

## 📦 Supported Providers

MemU works with **any OpenAI-compatible endpoint**. Here are some tested providers:

| Provider | Type | Base URL |
|----------|------|----------|
| **Ollama** | Local | `http://localhost:11434/v1` |
| **LMStudio** | Local | `http://localhost:1234/v1` |
| **OpenRouter** | Cloud | `https://openrouter.ai/api/v1` |
| **DeepInfra** | Cloud | `https://api.deepinfra.com/v1/openai` |
| **Fireworks AI** | Cloud | `https://api.fireworks.ai/inference/v1` |
| **OpenAI** | Cloud | `https://api.openai.com/v1` |
| **Custom** | Any | Your custom endpoint |

The system uses the standard OpenAI SDK, so if a provider supports the OpenAI API format, it will work with MemU.

## 🛠️ Installation

### Option 1: Automated Installer (Recommended)

#### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/NevaMind-AI/memU.git
cd memU

# Make the installer executable
chmod +x install.sh

# Run the installer
./install.sh
```

#### Windows

```cmd
# Clone the repository
git clone https://github.com/NevaMind-AI/memU.git
cd memU

# Run the installer
setup.bat
```

The installer will:
1. Check Docker installation
2. Guide you through provider selection
3. Create configuration files
4. Build the Docker image
5. Optionally start the container

### Option 2: Manual Setup

#### 1. Create Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure your provider. Example for Ollama:

```bash
MEMU_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3
```

For Docker, use `http://host.docker.internal:11434/v1` to access services running on your host.

#### 2. Build Docker Image

```bash
docker build -t memu-mcp-server .
```

#### 3. Run the Server

For testing:
```bash
docker run -i --rm \
  --env-file .env \
  -v $(pwd)/data:/data \
  memu-mcp-server
```

As a daemon:
```bash
docker run -d \
  --name memu-mcp \
  --env-file .env \
  -v $(pwd)/data:/data \
  memu-mcp-server
```

**Network Modes:**
- **Linux**: Add `--network=host` to access local services
- **macOS/Windows**: Use `host.docker.internal` in URLs (already configured in examples)

## 🔧 Configuration

### Environment Variables

The server supports configuration via environment variables or a `config.yaml` file.

#### Basic Configuration

```bash
# Provider Selection
MEMU_PROVIDER=ollama  # ollama | lmstudio | openrouter | deepinfra | fireworks | openai

# LLM Configuration
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=your_api_key_here
LLM_CHAT_MODEL=llama3
LLM_EMBED_MODEL=llama3

# Database
DB_PROVIDER=inmemory  # or postgres
# DB_DSN=postgresql://user:pass@localhost:5432/memu

# Retrieval Method
RETRIEVE_METHOD=rag  # or llm
```

#### Provider-Specific Examples

**Ollama (Local)**
```bash
MEMU_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1  # For Docker
OLLAMA_MODEL=llama3
OLLAMA_API_KEY=ollama
```

**OpenRouter**
```bash
MEMU_PROVIDER=openrouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

**OpenAI**
```bash
MEMU_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_CHAT_MODEL=gpt-4o-mini
LLM_EMBED_MODEL=text-embedding-3-small
```

### YAML Configuration (Advanced)

For more complex setups, use `config.yaml`:

```yaml
provider: "ollama"

llm_profiles:
  default:
    base_url: "http://host.docker.internal:11434/v1"
    api_key: "ollama"
    chat_model: "llama3"
    embed_model: "llama3"
    client_backend: "sdk"
  
  # Optional: Separate embedding provider
  embedding:
    base_url: "https://api.voyageai.com/v1"
    api_key: "${VOYAGE_API_KEY}"
    embed_model: "voyage-3.5-lite"

database_config:
  metadata_store:
    provider: "inmemory"

retrieve_config:
  method: "rag"
```

Set the config path:
```bash
export MEMU_CONFIG_PATH=/path/to/config.yaml
```

## 🔌 Using with MCP Clients

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "memu": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        "/Users/youruser/.memu/.env",
        "-v",
        "/Users/youruser/.memu/data:/data",
        "memu-mcp-server"
      ]
    }
  }
}
```

### Cursor

Similar configuration in Cursor's MCP settings.

### Custom MCP Clients

Any MCP client that supports stdio transport can connect to MemU. The server uses:
- **Transport**: stdio (standard input/output)
- **Protocol**: MCP 1.0
- **Format**: JSON-RPC

## 📚 Available Tools

### `memorize`
Process and extract structured memory from resources.

**Parameters:**
- `resource_url` (required): Path to the file or URL
- `modality` (required): Type of content - `conversation`, `document`, `image`, `video`, `audio`
- `user_id` (optional): User ID to scope the memory

**Example:**
```json
{
  "resource_url": "/path/to/conversation.json",
  "modality": "conversation",
  "user_id": "user123"
}
```

### `retrieve`
Query and retrieve relevant memories.

**Parameters:**
- `query` (required): Search query text
- `user_id` (optional): Filter by user ID
- `method` (optional): `rag` (fast) or `llm` (deep understanding)

**Example:**
```json
{
  "query": "What are the user's preferences?",
  "user_id": "user123",
  "method": "rag"
}
```

### `list_categories`
List all memory categories.

**Parameters:**
- `user_id` (optional): Filter by user ID

## 📊 Available Resources

### `memory://categories`
Returns all memory categories with descriptions.

### `memory://stats`
Returns statistics about the memory system.

## 💬 Available Prompts

### `analyze_conversation`
Pre-configured prompt for conversation analysis.

### `search_memories`
Pre-configured prompt for memory search.

## 🐳 Docker Management

### View Logs
```bash
docker logs -f memu-mcp
```

### Stop Server
```bash
docker stop memu-mcp
```

### Start Server
```bash
docker start memu-mcp
```

### Restart Server
```bash
docker restart memu-mcp
```

### Remove Container
```bash
docker rm -f memu-mcp
```

### Rebuild Image
```bash
docker build -t memu-mcp-server .
```

## 🔍 Troubleshooting

### Cannot connect to Ollama/LMStudio

**Problem**: Server can't reach local services.

**Solution**:
- **Linux**: Use `--network=host` when running Docker
- **macOS/Windows**: Use `host.docker.internal` instead of `localhost` in URLs

### MCP Client Connection Issues

**Problem**: Client can't connect to server.

**Solution**:
- Ensure Docker is running
- Check that the `.env` file exists and has valid configuration
- Verify the Docker command in your MCP client config is correct
- Check Docker logs for errors: `docker logs memu-mcp`

### Permission Errors

**Problem**: Can't write to data directory.

**Solution**:
- Ensure the data directory exists and is writable
- Check volume mount permissions
- On Linux, you may need to adjust the user in the Dockerfile

### Provider API Errors

**Problem**: Errors when calling the LLM.

**Solution**:
- Verify your API key is correct
- Check the base URL is correct for your provider
- Ensure the model name is valid
- Check if you have API credits/quota remaining

## 🤝 Contributing

We welcome contributions! Please see the main [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

[Apache License 2.0](LICENSE.txt)

## 🌐 Links

- [Main Repository](https://github.com/NevaMind-AI/memU)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [Discord Community](https://discord.gg/memu)
- [Documentation](https://memu.pro/docs)
