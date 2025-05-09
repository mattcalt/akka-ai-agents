import logging
import os # Import os to read environment variables
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from dotenv import load_dotenv

# Import the chat agent singleton and initialize it directly
from chat_agent.agent import agent as chat_agent_instance

# Load environment variables (ensure it's loaded)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_message(message_body: str, session_id: str, user_id: str):
    """Processes a single message using the ChatAgent directly, with provided session_id and user_id."""
    logger.info(f"Processing message: {message_body[:100]}... for session_id: {session_id}, user_id: {user_id}") 
    model_response_parts = [] # To store parts of the model's response
    
    try:
        # Use the provided session_id and user_id to create/initialize the agent session
        chat_agent_instance.create_new_session(session_id_override=session_id, user_id_override=user_id)
        logger.info(f"ChatAgent session set to: {session_id}, user_id: {user_id}")
        
        await chat_agent_instance.initialize() # Will use the session_id and user_id set by create_new_session
        
        # Get the initialized ChatAgent's actual LLM agent 
        actual_chat_agent = chat_agent_instance._agent 
        if actual_chat_agent is None:
             raise RuntimeError("ChatAgent has not been initialized properly.")

        # Create session service for this message processing run
        session_service = InMemorySessionService()
        
        session = session_service.create_session(
            app_name="queue_processor", 
            user_id="queue_trigger",
            session_id=session_id  # Now using the same session_id as ChatAgent
        )
        
        # Create runner with ChatAgent as the root agent
        runner = Runner(
            agent=actual_chat_agent, 
            app_name="queue_processor",
            session_service=session_service
        )
        
        # Prepare the initial message Content object with the actual request
        initial_message = Content(parts=[Part(text=message_body)])
        
        # Run the chat agent directly, passing the actual message content
        # as the initial message for the run.
        logger.info(f"Running ChatAgent for session: {session_id}")
        async for event in runner.run_async(
            new_message=initial_message, 
            user_id="queue_trigger", 
            session_id=session_id # Pass session_id to runner as well
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