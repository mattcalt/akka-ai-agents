from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
import os
import logging
from dotenv import load_dotenv
from contextlib import AsyncExitStack
import uuid

from .tools import create_all_tools
from . import prompt

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

class CoordinatorAgent:
    SUPPORTED_CONTENT_TYPES = ["text/plain", "application/json"]

    def __init__(self):
        self._agent = None
        self._exit_stack = AsyncExitStack()
        # We'll initialize these when creating a new session now, not at class init
        self.session_id = None
        logger.info("Initialized CoordinatorAgent factory")

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
        all_session_tools = create_all_tools()

        self.coding_llm = LiteLlm(
            model='litellm_proxy/gemini-2.5-pro-preview-05-06', #add litellm_proxy/ to force proxy usage
            api_base=os.environ['OPENAI_BASE'],
            api_key=os.environ['OPENAI_KEY'],
            user="coding_agent",
            extra_body={
                "metadata": {
                        "session_id": self.session_id  # Pass the session ID
                }
            }
        )

        self.general_llm = LiteLlm(
            model='litellm_proxy/gpt-4o-mini',
            api_base=os.environ['OPENAI_BASE'],
            api_key=os.environ['OPENAI_KEY'],
            user="coding_agent",
            extra_body={
                "metadata": {
                        "session_id": self.session_id  # Pass the session ID
                }
            }
        )

        codingAgent = LlmAgent(
            name="coding_agent",
            model=self.coding_llm,
            description="An autonomous coding agent that can write code, interact with GitHub, and execute commands.",
            tools=list(all_session_tools.values()),
            instruction=prompt.CODING_AGENT_PROMPT
        )

        solutionArchitectAgent = LlmAgent(
            name="solution_architect_agent",
            model=self.coding_llm,
            tools=list(all_session_tools.values()),
            description="An agent that can break down GitHub issues into smaller, easily consumable tasks.",
            instruction=prompt.SOLUTION_ARCHITECT_PROMPT,
            output_key="solution_plan"
        )

        designPipelineAgent = SequentialAgent(
            name="design_pipeline_agent",
            sub_agents=[solutionArchitectAgent, codingAgent],
            description="A pipeline agent that can coordinate the solution architect and the coding agent.",
        )


        coordinatorAgent = LlmAgent(
            name="coordinator_agent",
            model=self.general_llm,
            description="A coordinator agent that can coordinate the design pipeline agent and the coding agent.",
            before_model_callback=inject_initial_message_callback,
            instruction=prompt.COORDINATOR_AGENT_PROMPT,
            sub_agents=[designPipelineAgent]
        )

        #Other agents above, but only using the chat agent for testing purposes
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
agent = CoordinatorAgent()

async def get_root_agent():
    return await agent.root_agent

root_agent = get_root_agent 