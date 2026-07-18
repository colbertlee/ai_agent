from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import os

from agent import AIAgent

app = FastAPI(title="AI Agent API", version="1.0.0")

agent = None

def get_agent():
    global agent
    if agent is None:
        agent = AIAgent()
    return agent

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str

@app.get("/")
async def root():
    return FileResponse("web/index.html")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/tools")
async def get_tools():
    agent = get_agent()
    tools = agent.get_tools_list()
    return {"tools": [{"name": t} for t in tools]}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    agent = get_agent()
    session_id = request.session_id or str(uuid.uuid4())
    result = agent.run(request.message)
    return ChatResponse(message=result, session_id=session_id)

@app.websocket("/api/chat/stream")
async def chat_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            session_id = data.get("session_id", str(uuid.uuid4()))
            if not message:
                continue
            agent = get_agent()
            for chunk in agent.run_stream(message):
                await websocket.send_json({"type": "chunk", "data": chunk, "session_id": session_id})
            await websocket.send_json({"type": "complete", "session_id": session_id})
    except WebSocketDisconnect:
        pass

@app.post("/api/clear")
async def clear_history():
    agent = get_agent()
    return {"success": True, "message": agent.clear_history()}

@app.get("/api/api-key/status")
async def get_api_key_status():
    return get_agent().get_api_key_status()

@app.post("/api/api-key")
async def set_api_key(request: dict):
    agent = get_agent()
    agent.set_api_key(request.get("api_key", "").strip())
    return {"success": True, "configured": bool(agent.api_key)}

os.makedirs("web", exist_ok=True)
app.mount("/web", StaticFiles(directory="web"), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
