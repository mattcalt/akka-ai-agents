using Akka.Actor;
using AkkaAgents.Utilities;

namespace AkkaAgents
{
    public class ChatAgent : ReceiveActor
    {
        private readonly PythonScriptExecutor _scriptExecutor;
        
        public ChatAgent()
        {
            // The PythonScriptExecutor's static constructor will handle PythonEngine initialization once.
            // This instance will load "Scripts/script.py".
            _scriptExecutor = new PythonScriptExecutor("Scripts/script.py");

            Receive<string>(message =>
            {
                if (!_scriptExecutor.IsScriptLoaded)
                {
                    Console.WriteLine($"ChatAgent: Python script was not loaded by PythonScriptExecutor. Cannot process message: {message}");
                    // Potentially tell the sender about the failure if this actor is part of a request/reply flow.
                    // Sender.Tell(new ScriptProcessingError($"Script not loaded, cannot process: {message}"));
                    return;
                }

                string? response = _scriptExecutor.ExecuteFunction("process_message", message);

                if (response != null)
                {
                    Console.WriteLine($"ChatAgent received: {message}, Python responded: {response}");
                }
                else
                {
                    // Error details would have been logged by PythonScriptExecutor
                    Console.WriteLine($"ChatAgent: Failed to get a response from Python for message: {message}");
                }

                // After processing, the ChatAgent stops itself.
                Console.WriteLine($"ChatAgent ({Self.Path.Name}): Processed message. Stopping self.");
                Context.Stop(Self);
            });
        }

        protected override void PreStart()
        {
            base.PreStart();
            Console.WriteLine("ChatAgent started.");
            if (!_scriptExecutor.IsScriptLoaded) // Check status after executor is created
            {
                 Console.WriteLine("ChatAgent: Critical - Python script was not loaded by PythonScriptExecutor during ChatAgent construction. Check previous errors from PythonScriptExecutor.");
            }
        }

        protected override void PostStop()
        {
            // If _scriptExecutor needed explicit cleanup, we could call _scriptExecutor.Dispose() here.
            // However, for this implementation of PythonScriptExecutor, Dispose() is a no-op.
            base.PostStop();
            Console.WriteLine("ChatAgent stopped.");
        }
    }
} 