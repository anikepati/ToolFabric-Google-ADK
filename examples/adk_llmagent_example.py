import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from src.tool_fabric import ToolFabric  # From our ToolFabric package

# Optional: For structured inputs (Pydantic)
from pydantic import BaseModel, Field

class UserQueryInput(BaseModel):
    user_id: int = Field(description="User ID for info retrieval")

async def main():
    # Step 1: Load tools using ToolFabric
    fabric = ToolFabric("examples/config.yml")
    fabric.setup()  # Starts tools, health checks, etc.
    
    # Collect ToolFabric's tools as a list (ADK expects list of callables)
    tool_list = list(fabric.tools.values())  # e.g., [user_info_func, playwright_func, ...]
    
    # Step 2: Define agent instructions (guides LLM on tool usage)
    agent_instructions = """
    You are a helpful enterprise assistant for user management and web tasks.
    - For user queries (e.g., "Get info on user 123"), use the 'user_info' tool with user_id.
    - For web navigation (e.g., "Go to example.com"), use the 'playwright' tool with action='goto' and payload={'url': '...'}.
    - For server tasks, use 'local_server'.
    Always respond clearly after tool use. If no tool fits, explain why.
    """
    
    # Step 3: Create LlmAgent with tools
    agent = LlmAgent(
        model="gemini-2.0-flash",  # Or your Vertex AI model
        name="EnterpriseLlmAgent",
        description="Multi-tool agent for enterprise tasks",
        instruction=agent_instructions,
        tools=tool_list,  # Attach all ToolFabric tools here
        input_schema=UserQueryInput  # Optional: Enforce structured inputs
    )
    
    # Step 4: Set up session and runner
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name="enterprise_app", 
        user_id="demo_user", 
        session_id="demo_session"
    )
    runner = Runner(
        agent=agent, 
        app_name="enterprise_app", 
        session_service=session_service
    )
    
    # Step 5: Invoke the agent with a user query
    user_query = "What's the info for user ID 456?"
    user_content = types.Content(
        role='user', 
        parts=[types.Part(text=user_query)]
    )
    
    print(f"User Query: {user_query}")
    async for event in runner.run_async(
        user_id="demo_user", 
        session_id="demo_session", 
        new_message=user_content
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text
            print("Agent Response:", response_text)
            break  # Or process streaming events
    
    # Teardown
    fabric.stop_all()

if __name__ == "__main__":
    asyncio.run(main())
