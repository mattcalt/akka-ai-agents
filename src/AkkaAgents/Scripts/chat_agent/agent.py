from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import os
import logging
from dotenv import load_dotenv
from contextlib import AsyncExitStack
# import uuid # No longer generating UUIDs here

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Callback Function --- 
def inject_initial_message_callback(callback_context, llm_request):
    """Callback to inject initial user message if Contents are empty."""
    is_first_turn = not llm_request.contents
    if is_first_turn:
        logger.warning("Detected empty Contents in first LLM request. Injecting initial message.")
        user_content = getattr(callback_context, 'user_content', None)
        if user_content:
            user_content.role = 'user' 
            llm_request.contents.append(user_content)
            logger.info(f"Injected user content: {user_content}")
        else:
            logger.error("Callback triggered for empty Contents, but user_content not found in callback_context!")
# ------------------------

class ChatAgent:
    SUPPORTED_CONTENT_TYPES = ["text/plain", "application/json"]

    def __init__(self):
        # No per-instance session_id or user_id. These will be passed per call.
        self._exit_stack = AsyncExitStack() # Reusable for context management if needed
        logger.info("Initialized ChatAgent factory (now stateless regarding session/user IDs)")
    
    async def _build_agent(self, session_id_for_build: str, user_id_for_build: str):
        if not session_id_for_build or not user_id_for_build:
            raise ValueError("session_id_for_build and user_id_for_build must be provided to _build_agent.")
        
        logger.info(f"_build_agent: Building with session_id: {session_id_for_build}, user_id: {user_id_for_build}")

        current_llm = LiteLlm(
            model='gpt-4o-mini',
            api_base=os.environ['OPENAI_BASE'],
            api_key=os.environ['OPENAI_KEY'],
            user=user_id_for_build,
            extra_body={ # Used for Langfuse data
                "metadata": {
                        "session_id": session_id_for_build,
                        "user_id": user_id_for_build 
                }
            }
        )

        built_agent = LlmAgent(
            name="chat_agent",
            model=current_llm,
            description="An agent that can chat with the user.",
            before_model_callback=inject_initial_message_callback,
            instruction="You are a helpful assistant that can answer questions and help with tasks.",
        )
        # The exit_stack is for managing resources that current_llm or built_agent might need.
        # If they don't register anything with it, it's benign.
        return built_agent, self._exit_stack 

    async def initialize(self, session_id: str, user_id: str):
        """Initializes and returns a new LlmAgent instance configured with the provided session and user IDs."""
        if not session_id or not user_id:
            raise ValueError("session_id and user_id are mandatory for initialize.")
        
        logger.info(f"ChatAgent.initialize: Creating new agent for session_id: {session_id}, user_id: {user_id}")
        # Always build a new agent for each initialization, ensuring fresh state for the call.
        # The returned agent from _build_agent IS the one to use for the current request.
        initialized_agent, exit_stack = await self._build_agent(session_id_for_build=session_id, user_id_for_build=user_id)
        return initialized_agent # Return the agent directly

# Create singleton instance of the factory/helper class
agent_factory = ChatAgent() # Renamed to clarify its role

# Remove old root_agent as it's not compatible with per-request ID passing
# async def get_root_agent():
#     return await agent.root_agent
# root_agent = get_root_agent 