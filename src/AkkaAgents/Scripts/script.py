import logging
import os # Import os to read environment variables
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from dotenv import load_dotenv

# Import the chat agent factory
from chat_agent.agent import agent_factory # Use the renamed agent_factory

# Load environment variables (ensure it's loaded)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_message(message_body: str, session_id: str, user_id: str):
    """Processes a single message using a newly initialized ChatAgent for the provided session_id and user_id."""
    logger.info(f"Processing message: {message_body[:100]}... for session_id: {session_id}, user_id: {user_id}") 
    model_response_parts = [] # To store parts of the model's response
    
    try:
        # Initialize a new agent instance for this specific request using the factory
        # This agent is configured with the current request's session_id and user_id.
        current_chat_agent = await agent_factory.initialize(session_id=session_id, user_id=user_id)
        
        if current_chat_agent is None:
             raise RuntimeError("ChatAgent could not be initialized properly with provided IDs.")

        session_service = InMemorySessionService()
        
        # The session for the runner should also use the specific session_id
        runner_session = session_service.create_session(
            app_name="queue_processor", 
            user_id=user_id, # Pass user_id here as well
            session_id=session_id
        )
        
        runner = Runner(
            agent=current_chat_agent, # Use the agent initialized for this request
            app_name="queue_processor",
            session_service=session_service
        )
        
        # Prepare the initial message Content object with the actual request
        initial_message = Content(parts=[Part(text=message_body)])
        
        # Run the chat agent directly, passing the actual message content
        # as the initial message for the run.
        logger.info(f"Running ChatAgent for session: {session_id}, user_id: {user_id}")
        async for event in runner.run_async(
            new_message=initial_message, 
            user_id=user_id, # Pass user_id to runner
            session_id=session_id
        ):
            logger.info(f"[Session: {session_id}] Event: {event}")
            # Check if the event is from the chat_agent, its content is from the model, and has text
            if (hasattr(event, 'author') and event.author == "chat_agent" and
                hasattr(event, 'content') and event.content is not None and
                hasattr(event.content, 'role') and event.content.role == "model" and
                hasattr(event.content, 'parts') and event.content.parts is not None):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text is not None and part.text.strip() != "":
                        logger.info(f"Appending model part: '{part.text[:50]}...'") # Log what's being appended
                        model_response_parts.append(part.text)
            
        logger.info(f"Finished processing message for session: {session_id}")

        if model_response_parts:
            return "".join(model_response_parts)
        else:
            return "Agent did not provide a textual response."

    except Exception as e:
        logger.error(f"Error processing message: {message_body[:100]}... Error: {e}", exc_info=True)
        # Return the error message to C#
        return f"Error in Python script: {str(e)}"