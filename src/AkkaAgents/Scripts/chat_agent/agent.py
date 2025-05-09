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
        self.session_id = None
        self.user_id = None # Initialize user_id
        logger.info("Initialized ChatAgent factory")

    def create_new_session(self, session_id_override=None, user_id_override=None):
        """Creates/sets session ID and user ID."""
        if session_id_override:
            self.session_id = session_id_override
            logger.info(f"Using provided session ID: {self.session_id}")
        else:
            self.session_id = str(uuid.uuid4())
            logger.info(f"Created new agent session (generated): {self.session_id}")
        
        if user_id_override:
            self.user_id = user_id_override
            logger.info(f"Using provided user ID: {self.user_id}")
        else:
            self.user_id = f"default_user_{self.session_id[:8]}" # Default if not provided
            logger.info(f"Using default generated user ID: {self.user_id}")

        self._agent = None 
        return self.session_id, self.user_id
    
    @property
    async def root_agent(self):
        if self._agent is None:
            if not self.session_id or not self.user_id:
                self.create_new_session()
            await self._build_agent()
        return self._agent, self._exit_stack
    
    async def _build_agent(self):
        if not self.session_id or not self.user_id:
            logger.warning("session_id or user_id not set before _build_agent. Attempting to set defaults.")
            # Fallback, though create_new_session should be called via initialize
            self.create_new_session(session_id_override=self.session_id, user_id_override=self.user_id)

        self.general_llm = LiteLlm(
            model='gpt-4o-mini',
            api_base=os.environ['OPENAI_BASE'],
            api_key=os.environ['OPENAI_KEY'],
            user=self.user_id, # Use the instance's user_id
            extra_body={
                "metadata": {
                        "session_id": self.session_id,  # Pass the session ID
                        "user_id": self.user_id  # Pass the user_id
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

    async def initialize(self, session_id_override=None, user_id_override=None):
        """Initialize the agent, using overridden session and user IDs if provided."""
        # Ensure session_id and user_id are set, potentially using overrides
        if not self.session_id or session_id_override or not self.user_id or user_id_override:
            self.create_new_session(session_id_override=session_id_override, user_id_override=user_id_override)
        
        if self._agent is None:
            self._agent, self._exit_stack = await self._build_agent()

# Create singleton instance
agent = ChatAgent()

async def get_root_agent():
    return await agent.root_agent

root_agent = get_root_agent 