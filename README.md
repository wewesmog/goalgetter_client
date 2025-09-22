# Goalgetter Client

A production-ready productivity assistant that combines PydanticAI, MCP (Model Context Protocol), LangGraph, and Logfire for comprehensive goal, habit, and progress management.

## 🚀 Features

- **PydanticAI**: Structured AI responses with type safety
- **MCP Integration**: External tool integration for database operations
- **LangGraph**: Complex workflow orchestration with memory
- **Logfire**: Comprehensive observability and tracing
- **PostgreSQL**: Persistent conversation memory
- **FastAPI**: REST API for external access
- **CLI**: Command-line interface for testing and development

## 📁 Detailed Project Structure

```
goalgetter-client/
├── 📁 config/                    # Configuration and settings
│   ├── __init__.py              # Config module initialization
│   ├── prompts.py               # System prompts for AI agents
│   └── settings.py              # Pydantic settings with environment variables
│
├── 📁 src/                       # Main source code
│   ├── __init__.py              # Source module initialization
│   │
│   ├── 📁 agents/               # AI agents and orchestration
│   │   ├── __init__.py          # Agents module exports
│   │   └── core.py              # ProductivityAgent & LangGraphOrchestrator
│   │
│   ├── 📁 api/                  # FastAPI REST API
│   │   ├── __init__.py          # API module initialization
│   │   ├── main.py              # FastAPI app with endpoints
│   │   └── models.py            # API request/response models
│   │
│   ├── 📁 cli/                  # Command-line interface
│   │   ├── __init__.py          # CLI module exports
│   │   └── cli.py               # Typer-based CLI commands
│   │
│   ├── 📁 models/               # Pydantic data models
│   │   ├── __init__.py          # Models module exports
│   │   ├── responses.py         # ProductivityResponse models
│   │   └── schemas.py           # Database schemas
│   │
│   ├── 📁 services/             # External services
│   │   ├── __init__.py          # Services module exports
│   │   ├── mcp_service.py       # MCP server integration
│   │   ├── memory_service.py    # PostgreSQL memory management
│   │   └── conversation_service.py # Conversation context building
│   │
│   └── 📁 utils/                # Utility functions
│       ├── __init__.py          # Utils module exports
│       ├── logging.py           # Logfire setup and configuration
│       ├── message_utils.py     # Message trimming and processing
│       └── token_utils.py       # Token counting utilities
│
├── 📁 tests/                     # Test suite
│   └── __init__.py              # Test module initialization
│
├── 📁 docs/                      # Documentation
│
├── 📁 scripts/                   # Deployment and utility scripts
│
├── 📄 mcp_client_pydantic.py    # Standalone MCP client (reference)
├── 📄 test_api.py               # API testing script
├── 📄 requirements.txt          # Production dependencies
├── 📄 requirements-dev.txt      # Development dependencies
├── 📄 pyproject.toml            # Project configuration
├── 📄 Dockerfile                # Docker container configuration
├── 📄 railway.toml              # Railway deployment config
├── 📄 env.example               # Environment variables template
└── 📄 README.md                 # This file
```

## 🏗️ Architecture Overview

### Core Components

1. **🤖 Agents (`src/agents/`)**
   - `ProductivityAgent`: PydanticAI agent with MCP tools
   - `LangGraphOrchestrator`: Workflow orchestration with memory

2. **🌐 API (`src/api/`)**
   - `main.py`: FastAPI application with chat endpoints
   - `models.py`: Request/response schemas

3. **🔧 Services (`src/services/`)**
   - `mcp_service.py`: MCP server integration for goalgetter
   - `memory_service.py`: PostgreSQL conversation memory
   - `conversation_service.py`: Context building and summarization

4. **📊 Models (`src/models/`)**
   - `responses.py`: Structured AI response models
   - `schemas.py`: Database and API schemas

5. **🛠️ Utils (`src/utils/`)**
   - `logging.py`: Logfire observability setup
   - `message_utils.py`: Message trimming and processing
   - `token_utils.py`: Token counting and management

6. **⚙️ Config (`config/`)**
   - `settings.py`: Environment-based configuration
   - `prompts.py`: AI system prompts

## 🔄 Data Flow

```
User Request → FastAPI → LangGraph → PydanticAI Agent → MCP Tools → Database
     ↓              ↓         ↓            ↓              ↓           ↓
   Response ← FastAPI ← LangGraph ← PydanticAI ← MCP Results ← Database
```

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd goalgetter-client
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your configuration
```

4. **Required environment variables:**
```env
OPENAI_API_KEY=your_openai_api_key
PGURL=postgresql://username:password@host:port/database
LOGFIRE_TOKEN=your_logfire_token
MCP_SERVER_PATH=D:\\goalgetter
```

## 🚀 Usage

### CLI Interface

**Interactive mode:**
```bash
python -m src.cli.cli interactive
```

**Test a single message:**
```bash
python -m src.cli.cli test "show me my goals"
```

**Check memory status:**
```bash
python -m src.cli.cli check-memory
```

**Start FastAPI server:**
```bash
python -m src.cli.cli serve
```

### FastAPI Server

**Start the server:**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**API Endpoints:**
- `POST /chat` - Send messages to the assistant
- `GET /memory/{user_id}` - Check memory status
- `GET /health` - Health check
- `GET /` - API information

### Example API Usage

**Send a chat message:**
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "show me my goals",
       "user_id": "123"
     }'
```

**Check memory status:**
```bash
curl "http://localhost:8000/memory/123"
```

## 🔧 Configuration

The application uses Pydantic Settings for configuration management. Key settings:

- **Performance**: Message trimming thresholds, token limits
- **Database**: PostgreSQL connection settings
- **Logging**: Logfire configuration
- **MCP**: Server path and timeout settings

## 📊 Observability

The application includes comprehensive observability through Logfire:

- **LLM Tracing**: Complete request/response visibility
- **Tool Calls**: MCP tool execution tracking
- **Performance**: Token usage and response times
- **Errors**: Detailed error logging and tracing

## 🧪 Testing

**Run tests:**
```bash
pytest tests/
```

**Run with coverage:**
```bash
pytest --cov=src tests/
```

**Test API manually:**
```bash
python test_api.py
```

## 🚀 Deployment

### Railway Deployment

1. **Connect to Railway:**
```bash
railway login
railway init
```

2. **Set environment variables in Railway dashboard**

3. **Deploy:**
```bash
railway up
```

### Docker Deployment

**Build and run:**
```bash
docker build -t goalgetter-client .
docker run -p 8000:8000 --env-file .env goalgetter-client
```

## 🔍 Development

**Install development dependencies:**
```bash
pip install -r requirements-dev.txt
```

**Code formatting:**
```bash
black src/
isort src/
```

**Type checking:**
```bash
mypy src/
```

**Linting:**
```bash
flake8 src/
```

## 📚 Key Files Explained

### `src/agents/core.py`
- **ProductivityAgent**: Main AI agent with PydanticAI + MCP integration
- **LangGraphOrchestrator**: Manages conversation flow and memory
- **Message Trimming**: Automatically trims long conversations
- **Context Building**: Creates conversation summaries and context

### `src/api/main.py`
- **FastAPI Application**: REST API with chat endpoints
- **Lifespan Management**: Handles startup/shutdown with PostgreSQL
- **Error Handling**: Comprehensive error handling and logging
- **Response Formatting**: Clean response extraction from PydanticAI

### `src/services/mcp_service.py`
- **MCP Integration**: Connects to goalgetter MCP server
- **Tool Management**: Handles MCP tool calls and responses
- **Error Handling**: Robust MCP connection management

### `src/services/memory_service.py`
- **PostgreSQL Memory**: Manages conversation persistence
- **Checkpointer Setup**: Configures LangGraph memory
- **Memory Fallback**: Falls back to in-memory if PostgreSQL fails

### `config/settings.py`
- **Environment Variables**: All configuration via .env file
- **Pydantic Settings**: Type-safe configuration management
- **Performance Tuning**: Message trimming and token limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in `/docs`
- Review the API documentation at `/docs` when running the server