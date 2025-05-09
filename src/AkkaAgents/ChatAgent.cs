using Akka.Actor;
using Python.Runtime;
using System;
using System.IO;

namespace AkkaAgents
{
    public class ChatAgent : ReceiveActor
    {
        private dynamic? _pythonScript;

        public ChatAgent()
        {
            // Initialize Python engine if not already initialized
            if (!PythonEngine.IsInitialized)
            {
                PythonEngine.Initialize();
                PythonEngine.BeginAllowThreads(); // Important for Akka.NET
            }

            // Load the Python script
            var scriptPath = Path.Combine(AppContext.BaseDirectory, "script.py");
            if (!File.Exists(scriptPath))
            {
                Console.WriteLine($"Error: Python script not found at {scriptPath}. ChatAgent will not process messages via Python.");
                // _pythonScript remains null
            }
            else
            {
                try
                {
                    using (Py.GIL()) // Acquire the Global Interpreter Lock
                    {
                        // Add the directory of the script to Python's sys.path
                        // to ensure modules in the same directory can be imported if needed.
                        dynamic sys = Py.Import("sys");
                        sys.path.append(AppContext.BaseDirectory);
                        _pythonScript = Py.Import(Path.GetFileNameWithoutExtension(scriptPath));
                    }
                }
                catch (PythonException ex)
                {
                    Console.WriteLine($"PythonException during script import in ChatAgent: {ex.Message}");
                    Console.WriteLine($"Python StackTrace: {ex.StackTrace}");
                    if (ex.InnerException != null)
                    {
                        Console.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                    }
                     // _pythonScript remains null
                }
                catch (Exception ex)
                {
                     Console.WriteLine($"Generic Exception during script import in ChatAgent: {ex.Message}");
                     // _pythonScript remains null
                }
            }

            Receive<string>(message =>
            {
                if (_pythonScript == null)
                {
                    Console.WriteLine($"ChatAgent cannot process message: Python script was not loaded successfully.");
                    // Optionally, you could send a failure message back to the sender
                    // Sender.Tell(new ScriptProcessingFailed(message, "Python script not loaded"));
                    return;
                }

                string response = "Error processing message with Python.";
                try
                {
                    using (Py.GIL()) // Acquire GIL for this operation
                    {
                        dynamic result = _pythonScript.InvokeMethod("process_message", new PyString(message));
                        response = result.ToString();
                    }
                    Console.WriteLine($"ChatAgent received: {message}, Python responded: {response}");
                }
                catch (PythonException ex)
                {
                    Console.WriteLine($"PythonException in ChatAgent: {ex.Message}");
                    Console.WriteLine($"Python StackTrace: {ex.StackTrace}");
                     if (ex.InnerException != null)
                    {
                        Console.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Exception in ChatAgent: {ex.Message}");
                }
            });
        }

        protected override void PreStart()
        {
            base.PreStart();
            Console.WriteLine("ChatAgent started.");
            if (_pythonScript == null)
            {
                 Console.WriteLine("ChatAgent started, but Python script was not loaded. Check previous errors.");
            }
        }

        protected override void PostStop()
        {
            // PythonEngine.Shutdown(); // Typically shutdown when the ActorSystem terminates
            base.PostStop();
            Console.WriteLine("ChatAgent stopped.");
        }
    }
} 