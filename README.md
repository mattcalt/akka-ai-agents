# Akka.NET Agents with Python Integration

This project demonstrates an Akka.NET application that integrates with Python scripts using Python.NET. It includes a `ChatAgent` actor capable of executing functions within a Python script.

## Prerequisites

1.  **.NET SDK:** Version 8.0 or later.
2.  **Python:** Version 3.13 (as configured). Ensure it's installed and accessible. This project was developed using Python from Homebrew on macOS.
3.  **Python Virtual Environment:** The project is set up to use a Python virtual environment for managing Python dependencies.

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd akka-ai-agents 
    ```

2.  **Create and Activate Python Virtual Environment:**
    From the project root directory (`akka-ai-agents`):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    *(On Windows, activation is `.venv\Scripts\activate`)*

3.  **Install Python Dependencies:**
    While the virtual environment is active, install required packages. For the example `script.py`:
    ```bash
    pip install emoji
    ```
    *(Add any other dependencies your Python scripts might need here.)*

4.  **Set Environment Variables:**
    Before running the .NET application, you **must** set the following environment variables in your terminal session where you intend to run `dotnet run`. **Ensure your virtual environment is active when setting these.**

    *   **`PYTHONNET_PYDLL`**: Path to your Python shared library.
        *   For Homebrew Python 3.13 on macOS (example):
            ```bash
            export PYTHONNET_PYDLL="/opt/homebrew/Frameworks/Python.framework/Versions/3.13/lib/libpython3.13.dylib"
            ```
        *   Adjust this path based on your Python installation location and version.

    *   **`PYTHONHOME`**: Path to the root of your Python installation's library structure.
        *   For Homebrew Python 3.13 on macOS (example):
            ```bash
            export PYTHONHOME="/opt/homebrew/Cellar/python@3.13/3.13.3/Frameworks/Python.framework/Versions/3.13"
            ```
        *   Adjust this path based on your Python installation. It's often the directory containing `lib` and `include` for your Python version.

    *   **Optional: `PYTHONPATH`** (for reference, primarily handled by C# code)
        The C# code dynamically adds necessary paths to Python's `sys.path`. However, if you were running Python scripts directly or for other tools, `PYTHONPATH` would point to your venv's `site-packages` and any script directories. For this application, the C# code appends:
        *   The application's output directory (e.g., `src/AkkaAgents/bin/Debug/net8.0/`) for the main script.
        *   The venv's `site-packages` directory (e.g., `.venv/lib/python3.13/site-packages/`).
        If you were to set it manually for other purposes:
        ```bash
        # export PYTHONPATH="/path/to/your/project/.venv/lib/python3.13/site-packages:/path/to/your/project/src/AkkaAgents/bin/Debug/net8.0" 
        ```

    **Note:** These environment variables are set for the current terminal session. For persistent settings, add them to your shell's profile script (e.g., `~/.zshrc`, `~/.bash_profile`, or PowerShell profile).

## Running the Application

1.  **Ensure Prerequisites and Setup steps are complete.**
2.  **Activate your virtual environment:**
    ```bash
    source .venv/bin/activate
    ```
3.  **Set the required environment variables** (`PYTHONNET_PYDLL`, `PYTHONHOME`) in the same terminal session.
4.  **Navigate to the .NET project directory:**
    ```bash
    cd src/AkkaAgents
    ```
5.  **Run the application:**
    ```bash
    dotnet run
    ```

You should see output from the Akka.NET system, including messages processed by the `ChatAgent` via the Python script.

## Project Structure

*   `src/AkkaAgents/`: Contains the .NET Akka application.
    *   `ChatAgent.cs`: Example actor that uses Python.
    *   `Utilities/PythonScriptExecutor.cs`: Helper class for Python.NET interaction.
    *   `Scripts/script.py`: Example Python script called by `ChatAgent`.
    *   `Program.cs`: Main entry point for the .NET application.
    *   `AkkaAgents.csproj`: Project file.
*   `.venv/`: Python virtual environment (created locally, ignored by Git).
*   `.gitignore`: Specifies intentionally untracked files.
*   `README.md`: This file.

## Troubleshooting Python.NET

*   **`No module named 'encodings'`**: `PYTHONHOME` is likely not set or incorrect.
*   **`BadPythonDllException` or `Failed to load symbol Py_IncRef`**: `PYTHONNET_PYDLL` is likely not set or incorrect, or points to an incompatible Python library.
*   **`No module named 'your_script_name'`**:
    *   Ensure the script is being copied to the output directory (check `.csproj`).
    *   Ensure `AppContext.BaseDirectory` (where the host .NET app runs) is effectively part of Python's `sys.path` when the script is imported. The `PythonScriptExecutor` attempts to add this.
*   **`No module named 'your_python_package'` (e.g., `emoji`)**:
    *   Ensure the package is installed in the correct virtual environment (`.venv/lib/python3.13/site-packages`).
    *   Ensure the path to this `site-packages` directory is correctly added to Python's `sys.path` by `PythonScriptExecutor.cs`.
    *   Verify `PYTHONHOME` is correctly set. 