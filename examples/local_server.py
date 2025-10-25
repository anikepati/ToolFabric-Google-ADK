# examples/local_server.py
# A lightweight, fast MCP server using FastAPI for SSE (Server-Sent Events) support.
# This implements a basic MCP endpoint that echoes actions/payloads and sends periodic pings.
# Requirements: pip install fastapi uvicorn[standard]
# Run: uvicorn local_server:app --host 0.0.0.0 --port 9090 --reload (but for subprocess, just python local_server.py)

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import uvicorn
from typing import AsyncGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fast MCP Server")

# In-memory store for simplicity (use Redis in prod for multi-client)
clients = set()

async def sse_generator(client_id: str) -> AsyncGenerator[str, None]:
    """SSE event generator: handles incoming messages via POST, sends responses/events."""
    while True:
        try:
            # Simulate periodic health ping every 10s
            yield f"data: {json.dumps({'type': 'ping', 'from': 'server', 'client': client_id})}\n\n"
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            logger.info(f"SSE client {client_id} disconnected")
            break

@app.post("/mcp/action")
async def handle_mcp_action(request: Request):
    """MCP action endpoint: receives {action, payload}, echoes back via SSE."""
    try:
        body = await request.json()
        action = body.get("action")
        payload = body.get("payload", {})
        client_id = body.get("client_id", "unknown")
        
        logger.info(f"Received MCP action: {action} from {client_id}, payload: {payload}")
        
        # Echo response (in real: process action, e.g., run command)
        response = {
            "type": "response",
            "action": action,
            "status": "success",
            "result": f"Echo: {action} with {payload}",
            "to": client_id
        }
        
        # Broadcast to all SSE clients (or target specific)
        for client in clients:
            # In real: send via client-specific channel
            pass  # Placeholder: log instead
        logger.info(f"Sent response: {response}")
        
        return {"status": "processed", "response": response}
    except Exception as e:
        logger.error(f"MCP action error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/mcp/sse/{client_id}")
async def sse_stream(client_id: str):
    """SSE endpoint for MCP events."""
    clients.add(client_id)
    logger.info(f"SSE connection established for {client_id}")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        async for data in sse_generator(client_id):
            yield data
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.on_event("shutdown")
async def shutdown_event():
    clients.clear()
    logger.info("MCP server shutdown")

if __name__ == "__main__":
    # Run with uvicorn for ASGI
    uvicorn.run(app, host="localhost", port=9090, log_level="info")
