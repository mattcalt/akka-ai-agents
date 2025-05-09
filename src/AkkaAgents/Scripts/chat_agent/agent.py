from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import os
import logging
from dotenv import load_dotenv
from contextlib import AsyncExitStack
import uuid


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
        self._agent = None
        self._exit_stack = AsyncExitStack()
        # We'll initialize these when creating a new session now, not at class init
        self.session_id = None
        logger.info("Initialized ChatAgent factory")

    def create_new_session(self):
        """Creates a new session with unique ID"""
        self.session_id = str(uuid.uuid4())
        logger.info(f"Created new agent session {self.session_id}")
        # Reset agent so it will be recreated with the new session context
        self._agent = None
        return self.session_id
    
    @property
    async def root_agent(self):
        if self._agent is None:
            # Ensure we have a session
            if not self.session_id:
                self.create_new_session()
            await self._build_agent()
        return self._agent, self._exit_stack
    
    async def _build_agent(self):

        self.general_llm = LiteLlm(
            model='gpt-4o-mini',
            api_base=os.environ['OPENAI_BASE'],
            api_key=os.environ['OPENAI_KEY'],
            user="coding_agent",
            extra_body={
                "metadata": {
                        "session_id": self.session_id  # Pass the session ID
                }
            }
        )

        self._agent = LlmAgent(
            name="chat_agent",
            model=self.general_llm,
            description="An agent that can chat with the user.",
            before_model_callback=inject_initial_message_callback,
            instruction="You are a helpful assistant that can answer questions and help with tasks.",
        )

        return self._agent, self._exit_stack

    async def initialize(self):
        """Initialize the agent with a new session if needed."""
        if not self.session_id:
            self.create_new_session()
        if self._agent is None:
            self._agent, self._exit_stack = await self._build_agent()

# Create singleton instance
agent = ChatAgent()

async def get_root_agent():
    return await agent.root_agent

root_agent = get_root_agent 