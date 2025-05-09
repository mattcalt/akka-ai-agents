import logging
import os # Import os to read environment variables
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from dotenv import load_dotenv

# Import the coordinator agent singleton and initialize it directly
from coordinator_agent.agent import agent as coordinator_agent_instance

# Load environment variables (ensure it's loaded)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_message(message_body: str):
    """Processes a single message using the CoordinatorAgent directly."""
    logger.info(f"Processing message: {message_body[:100]}...") 
    
    try:
        # Create a new session for this message
        session_id = coordinator_agent_instance.create_new_session()
        logger.info(f"Created new CoordinatorAgent session: {session_id}")
        
        # Initialize the agent with the new session
        await coordinator_agent_instance.initialize()
        
        # Get the initialized CoordinatorAgent's actual LLM agent 
        actual_coordinator_agent = coordinator_agent_instance._agent 
        if actual_coordinator_agent is None:
             raise RuntimeError("CoordinatorAgent has not been initialized properly.")

        # Create session service for this message processing run
        session_service = InMemorySessionService()
        
        session = session_service.create_session(
            app_name="queue_processor", 
            user_id="queue_trigger",
            session_id=session_id  # Now using the same session_id as CoordinatorAgent
        )
        
        # Create runner with CoordinatorAgent as the root agent
        runner = Runner(
            agent=actual_coordinator_agent, 
            app_name="queue_processor",
            session_service=session_service
        )
        
        # Prepare the initial message Content object with the actual request
        initial_message = Content(parts=[Part(text=message_body)])
        
        # Run the coordinator agent directly, passing the actual message content
        # as the initial message for the run.
        logger.info(f"Running CoordinatorAgent for session: {session_id}")
        async for event in runner.run_async(
            new_message=initial_message, # Pass the REAL message content here
            user_id="queue_trigger", 
            session_id=session_id
        ):
            logger.info(f"[Session: {session_id}] Event: {event}")
            
        logger.info(f"Finished processing message for session: {session_id}")

        return "Message processed successfully"

    except Exception as e:
        logger.error(f"Error processing message: {message_body[:100]}... Error: {e}", exc_info=True)