# Travel Planner Assistant

An AI-powered travel planning assistant that helps users create personalized travel itineraries through conversation.

## Features
- Chat-based travel planning
- Persistent conversation history
- User authentication
- Real-time AI responses
- Multi-chat support

## Requirements
- Python 3.9+
- SQLite3
- Ollama (for LLM)

## Setup
### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run FastAPI Server
```bash
uvicorn backend.main:app --reload
```

### 3. Run Streamlit App
```bash
streamlit run frontend/app.py
```

## 4. Install Ollama
```bash
brew install ollama
```

## 5. Pull Ollama Models
```bash
ollama pull llama2
ollama pull tinyllama
```

## 6. Run Ollama
```bash
ollama serve
```
## 7. Open http://localhost:8501 in your browser and happy planning!
