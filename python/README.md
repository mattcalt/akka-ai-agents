# Pykka-based AI Agent System

This directory contains a pure Python implementation of an actor system using [Pykka](https://pykka.readthedocs.io/) to manage and interact with AI agents, specifically leveraging the Google Agent Development Kit (ADK). It serves as a Python-native alternative to an Akka.NET system that might integrate with Python via Python.NET.

## Purpose

The primary goal of this system is to demonstrate concurrent processing of multiple requests, where each request is handled by an AI agent. This setup is designed for scenarios requiring interaction with Large Language Models (LLMs) in a scalable and concurrent manner, entirely within the Python ecosystem.

## How It Works

The system is composed of the following key components and workflows:

1.  **`main.py` (Orchestrator)**:
    *   This script serves as the entry point and simulates a batch of concurrent requests.
    *   It initializes the Pykka actor system and an `AgentManagerActor`.
    *   It dispatches a configurable number of tasks in parallel. For each task:
        *   It asks the `AgentManagerActor` to create a new `AgentActor`.
        *   It sends a "process" message (containing the text to be processed) to the newly created `AgentActor`. This call is non-blocking (`ask(block=False)`), and a `Future` object is stored.
    *   After all tasks are dispatched, `main.py` iterates through the stored futures, waiting for each one to complete using `future.get()`.
    *   Once a task's result is retrieved, the corresponding `AgentActor` is stopped.
    *   This approach allows all `AgentActor` instances to perform their work (including LLM interactions) concurrently.

2.  **`AgentManagerActor` (`agent_manager_actor.py`)**:
    *   A Pykka `ThreadingActor` responsible for creating worker actors.
    *   When it receives a "create\_agent" message, it starts a new `AgentActor` instance, passing along a `session_id` (common for the batch) and a unique `user_id`.

3.  **`AgentActor` (`agent_actor.py`)**:
    *   A Pykka `ThreadingActor` that handles the actual processing of a single request.
    *   Its `on_receive` method is synchronous from Pykka's perspective. However, to interact with the asynchronous Google ADK methods, it uses `asyncio.run()` internally to call a helper async method (`_handle_async_processing`).
    *   The `_handle_async_processing` method:
        *   Uses the `agent_factory` from `agents.chat_agent.agent` to initialize an ADK `LlmAgent` configured for the current `session_id` and `user_id`.
        *   Utilizes the ADK `Runner` pattern to send the input text to the `LlmAgent` and process the resulting events to extract the model's response. This is the standard way to interact with ADK agents.
    *   Each `AgentActor` runs in its own thread, enabling concurrent execution of multiple LLM requests.

4.  **ADK Chat Agent (`agents/chat_agent/agent.py`)**:
    *   Contains the `ChatAgent` factory (`agent_factory`).
    *   This factory is responsible for creating and configuring instances of `google.adk.agents.LlmAgent`.
    *   It uses environment variables (`OPENAI_BASE`, `OPENAI_KEY`) to configure the underlying LLM (e.g., via LiteLLM or another OpenAI-compatible proxy).

## How to Use

### Prerequisites

*   Python 3.10 or newer.
*   `pip` for package installation.

### Setup

1.  **Navigate to the `python` directory**:
    ```bash
    cd /path/to/your/workspace/akka-ai-agents/python
    ```

2.  **Create and Activate a Python Virtual Environment**:
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    *(On Windows, activation is `.venv\\Scripts\\activate`)*

3.  **Install Dependencies**:
    With the virtual environment activated, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Environment Variables

Before running the application, you **must** set the following environment variables. You can do this by creating a `.env` file in the `python/` directory or by setting them directly in your terminal session.

*   **`OPENAI_BASE`**: The base URL for your LiteLLM instance or any other OpenAI-compatible proxy that your ADK `LlmAgent` will connect to.
    *   Example: `OPENAI_BASE="http://litellm.localtest.me"`
*   **`OPENAI_KEY`**: The API key for your LLM service. This can be a placeholder if your proxy manages the actual keys, but the variable should be set.
    *   Example: `OPENAI_KEY="your_llm_api_key_or_placeholder"`

Example `.env` file content (place in `python/.env`):
```env
OPENAI_BASE="http://localhost:8000"
OPENAI_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```
The `agents/chat_agent/agent.py` script uses `python-dotenv` to automatically load these variables from a `.env` file if present.

### Running the Application

1.  Ensure your virtual environment is active.
2.  Ensure the environment variables are set (or a `.env` file is present).
3.  From the **root of the workspace** (e.g., `akka-ai-agents/`), run:
    ```bash
    python python/main.py
    ```

You should see output indicating the start of the Pykka system, the dispatching of multiple tasks, logs from individual `AgentActor` instances (including logs from the ADK agent interactions), and finally, a summary of the responses.

## Project Structure (`python/` directory)

*   `main.py`: Main entry point; simulates concurrent requests to the actor system.
*   `agent_manager_actor.py`: Defines the `AgentManagerActor` for creating worker agents.
*   `agent_actor.py`: Defines the `AgentActor` which processes individual requests using the ADK agent.
*   `agents/`: Package containing ADK agent-related code.
    *   `chat_agent/`: Sub-package for the chat agent.
        *   `__init__.py`: Makes `chat_agent` a package and exports necessary symbols.
        *   `agent.py`: Contains the `ChatAgent` factory (`agent_factory`) for creating and configuring ADK `LlmAgent` instances.
    *   `__init__.py`: Makes `agents` a package.
*   `requirements.txt`: Lists Python dependencies (Pykka, google-adk, python-dotenv, litellm).
*   `README.md`: This file.

This setup provides a robust, pure-Python environment for developing and testing concurrent AI agent interactions. 