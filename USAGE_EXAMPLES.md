# MemU MCP Server Usage Examples

This document provides practical examples of using the MemU MCP Server.

## Quick Test Setup

### 1. Set up with Ollama (Local)

```bash
# Start Ollama (if not already running)
ollama serve

# Pull a model
ollama pull llama3

# Set environment variables
export MEMU_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434/v1
export OLLAMA_MODEL=llama3
export OLLAMA_API_KEY=ollama

# Run the MCP server (for testing in terminal)
python -m memu.mcp_server
```

### 2. Set up with OpenAI

```bash
# Set environment variables
export MEMU_PROVIDER=openai
export OPENAI_API_KEY=your_api_key_here
export LLM_CHAT_MODEL=gpt-4o-mini

# Run the MCP server
python -m memu.mcp_server
```

### 3. Set up with OpenRouter

```bash
# Set environment variables
export MEMU_PROVIDER=openrouter
export OPENROUTER_API_KEY=your_openrouter_key
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Run the MCP server
python -m memu.mcp_server
```

## Using with Claude Desktop

### macOS Configuration

1. Open Claude Desktop configuration file:
   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Add MemU MCP server:
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

3. Restart Claude Desktop

4. In Claude, you can now use prompts like:
   - "Analyze this conversation and save it to my memory"
   - "What do you remember about my preferences?"
   - "Search my memories for information about work habits"

### Windows Configuration

1. Open configuration file:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. Add MemU MCP server (adjust paths):
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
           "C:\\Users\\youruser\\.memu\\.env",
           "-v",
           "C:\\Users\\youruser\\.memu\\data:/data",
           "memu-mcp-server"
         ]
       }
     }
   }
   ```

### Linux Configuration

1. Configuration location:
   ```bash
   ~/.config/Claude/claude_desktop_config.json
   ```

2. Add MemU with host networking (for Ollama):
   ```json
   {
     "mcpServers": {
       "memu": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "--network=host",
           "--env-file",
           "/home/youruser/.memu/.env",
           "-v",
           "/home/youruser/.memu/data:/data",
           "memu-mcp-server"
         ]
       }
     }
   }
   ```

## Example Workflows

### Workflow 1: Personal Assistant Memory

1. **Save a conversation:**
   ```
   User: "Please remember that I prefer dark mode in all my applications and 
         I'm allergic to peanuts. Also, I work best in the mornings between 
         9am and 11am."
   
   Claude: (Using memorize tool)
   ```

2. **Retrieve preferences later:**
   ```
   User: "What are my UI preferences?"
   
   Claude: (Using retrieve tool) "You prefer dark mode in all applications."
   ```

### Workflow 2: Code Project Memory

1. **Save project structure:**
   ```
   User: "Remember that this project uses FastAPI for the backend, React for 
         the frontend, and PostgreSQL for the database. We follow REST API 
         conventions."
   
   Claude: (Using memorize tool with document modality)
   ```

2. **Query later:**
   ```
   User: "What database are we using in this project?"
   
   Claude: (Using retrieve tool) "This project uses PostgreSQL."
   ```

### Workflow 3: Meeting Notes

1. **Save meeting notes:**
   ```
   User: "Store these meeting notes: Discussed Q1 priorities - focus on 
         performance optimization, migrate to microservices, hire 2 backend 
         engineers. Action items: John to draft architecture proposal by 
         Friday."
   
   Claude: (Using memorize tool)
   ```

2. **Retrieve action items:**
   ```
   User: "What are the action items from recent meetings?"
   
   Claude: (Using retrieve tool) Shows action items with source conversations
   ```

## Advanced Configuration

### Using Config File Instead of Environment Variables

Create `config.yaml`:

```yaml
provider: "ollama"

llm_profiles:
  default:
    base_url: "http://localhost:11434/v1"
    api_key: "ollama"
    chat_model: "llama3"
    embed_model: "llama3"
    client_backend: "sdk"

database_config:
  metadata_store:
    provider: "inmemory"

retrieve_config:
  method: "rag"
```

Set the config path:
```bash
export MEMU_CONFIG_PATH=/path/to/config.yaml
python -m memu.mcp_server
```

### Using PostgreSQL for Persistence

```yaml
database_config:
  metadata_store:
    provider: "postgres"
    dsn: "postgresql://user:password@localhost:5432/memu"
```

Start PostgreSQL:
```bash
docker run -d \
  --name memu-postgres \
  -e POSTGRES_USER=memu \
  -e POSTGRES_PASSWORD=memu \
  -e POSTGRES_DB=memu \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Multiple LLM Profiles

```yaml
llm_profiles:
  # Fast, local model for embeddings
  embedding:
    base_url: "http://localhost:11434/v1"
    api_key: "ollama"
    embed_model: "nomic-embed-text"
    client_backend: "sdk"
  
  # Powerful cloud model for chat
  default:
    base_url: "https://openrouter.ai/api/v1"
    api_key: "${OPENROUTER_API_KEY}"
    chat_model: "anthropic/claude-3.5-sonnet"
    client_backend: "sdk"
```

## Troubleshooting

### Issue: "Cannot connect to Ollama"

**Solution for Docker:**
- Use `http://host.docker.internal:11434/v1` instead of `http://localhost:11434/v1`
- On Linux, add `--network=host` to docker run command

### Issue: "MCP server not responding"

**Debug steps:**
```bash
# Check server logs
docker logs memu-mcp

# Test server manually
docker run -i --rm --env-file .env memu-mcp-server

# Verify environment variables
docker run --rm --env-file .env memu-mcp-server env | grep MEMU
```

### Issue: "No memories found"

**Check:**
1. Verify data directory is mounted: `-v /path/to/data:/data`
2. Check database provider: `DB_PROVIDER=inmemory` or `postgres`
3. Ensure you're using the same user_id when storing and retrieving

## Performance Tips

1. **Use RAG for speed:**
   ```bash
   export RETRIEVE_METHOD=rag
   ```

2. **Use LLM for deep understanding:**
   ```bash
   export RETRIEVE_METHOD=llm
   ```

3. **Use local models for privacy:**
   - Ollama for chat and embeddings
   - LMStudio for models with GUIs
   - No data leaves your machine

4. **Use cloud models for quality:**
   - OpenRouter for access to multiple providers
   - OpenAI for GPT-4
   - Anthropic Claude via OpenRouter

## Security Best Practices

1. **Never commit .env files:**
   - Use `.env.example` as a template
   - Keep actual `.env` out of version control

2. **Secure API keys:**
   - Use environment variables
   - Rotate keys regularly
   - Use separate keys for dev/prod

3. **Data isolation:**
   - Use separate data directories per user
   - Consider encryption at rest for sensitive data
   - Use user_id scoping for multi-tenant setups

4. **Network security:**
   - Keep Ollama/LMStudio behind firewall
   - Use HTTPS for cloud providers
   - Consider VPN for remote access

## Next Steps

- Read [MCP_README.md](MCP_README.md) for comprehensive documentation
- Explore example conversations in `examples/`
- Join our [Discord](https://discord.gg/memu) for support
- Check out the [main README](README.md) for Python library usage
