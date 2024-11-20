# Travel Planner Assistant
An AI-powered travel planning assistant that helps users create personalized travel itineraries through conversation.

# Click here to see [demo](https://drive.google.com/file/d/1BHmZUJFx8jterQw4YHACxxMovGVaLbAy/view?usp=sharing)

* Note: Due to my endsemester exams, I am able to just meet basic requirements of the project. I will be updating the project with more features and improvements in the future.

## Requirements
- Python 3.9+
- SQLite3
- Ollama (for LLM)

## Architecture Overview

### Frontend (Streamlit)
- Built with [`app.py`](frontend/app.py)
- Uses Streamlit for the UI components and session management
- Features secure cookie-based authentication
- Real-time chat interface with message history
- Sidebar navigation for multiple chat sessions

### Backend (FastAPI)
- Core API server in [`main.py`](backend/main.py)
- JWT-based authentication system in [`auth.py`](backend/auth.py)
- SQLite database management in [`database.py`](backend/database.py)
- AI chat logic in [`chatbot.py`](backend/chatbot.py)

### Data Flow
1. **Authentication Flow**
   - User credentials → FastAPI `/login` or `/register` endpoints
   - JWT token generation and verification
   - Token stored in secure cookies and session state

2. **Chat Flow**
   - User message → Streamlit frontend
   - Request with auth token → FastAPI backend
   - Message processing with LLMs via Ollama:
        1. User Input → TinyLLAMA (Extracts key information from user prompt):
            - Location preferences
            - Date ranges
            - Budget constraints
            - Travel interests

        2. Processed Information → LLAMA2:
            - Generates detailed travel plans
            - Maintains conversation context
            - Provides recommendations
   - Response stored in database and returned to frontend

3. **Database Structure**
   - Users table: Authentication data
   - Chats table: Conversation sessions
   - Chat_messages table: Message history

### AI Implementation
- Uses Ollama with LLaMA2 model
- Context-aware travel planning using [`TravelContext`](backend/chatbot.py)
- Progressive information gathering for:
  - Location
  - Dates
  - Budget
  - Interests
- Dynamic prompt engineering based on missing information

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Ollama (below for macOS):
- In one terminal, Install Ollama using Homebrew and serve the server:
```bash
brew install ollama
ollama serve
```
- In another terminal, pull the LLaMA2 and TinyLLaMA models:
```bash
ollama pull llama2
ollama pull tinyllama
```

### 3. Run FastAPI Server
```bash
uvicorn backend.main:app --reload
```

### 4. Run Streamlit App
```bash
streamlit run frontend/app.py
```

### 5. Open http://localhost:8501 in your browser and happy planning!

### 6. Checkout my demo [here](https://drive.google.com/file/d/1BHmZUJFx8jterQw4YHACxxMovGVaLbAy/view?usp=sharing)

## Features
- Chat-based travel planning
- Persistent conversation history
- User authentication using **Json Web Tokens**
- Real-time AI responses
- Multi-chat support
- Weather preferences
- Budget constraints
- Location-based recommendations
- Date-based recommendations
- Interest-based recommendations
- Dynamic prompt generation

## Future Work
The project can be extended in the following ways:
- Implement more advanced AI models
- Add support for multiple languages
- Integrate with external APIs for real-time data
- Map-based itinerary visualization with Map APIs
- Admin panel for user management

## DataBase Schema
```sql
users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
)

chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username)
)

chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_input TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
)
```