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

            Receive<ProcessTextRequest>(request =>
            {
                if (!_scriptExecutor.IsScriptLoaded)
                {
                    Console.WriteLine($"ChatAgent ({Self.Path.Name}): Python script not loaded. Cannot process SessionId: {request.SessionId}, UserId: {request.UserId}, Message: {request.Text}");
                    Context.Stop(Self);
                    return;
                }

                Console.WriteLine($"ChatAgent ({Self.Path.Name}): Processing SessionId: {request.SessionId}, UserId: {request.UserId}, Message: '{request.Text.Substring(0, Math.Min(request.Text.Length, 20))}...'");
                string? response = _scriptExecutor.ExecuteFunction("process_message", request.Text, request.SessionId, request.UserId);

                if (response != null)
                {
                    Console.WriteLine($"ChatAgent ({Self.Path.Name}) received for SessionId {request.SessionId}, UserId {request.UserId}: '{request.Text.Substring(0, Math.Min(request.Text.Length, 20))}...', Python responded: {response}");
                }
                else
                {
                    Console.WriteLine($"ChatAgent ({Self.Path.Name}): Failed for SessionId {request.SessionId}, UserId {request.UserId}, Message: '{request.Text.Substring(0, Math.Min(request.Text.Length, 20))}...'");
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