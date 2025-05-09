using Akka.Actor;
using System;

namespace AkkaAgents
{
    // Define a message type for requests
    public record ProcessTextRequest(string Text, string SessionId, string UserId);

    public class RequestManagerActor : ReceiveActor
    {
        private int _requestCounter = 0;

        public RequestManagerActor()
        {
            // This actor now expects a ProcessTextRequest from Program.cs
            Receive<ProcessTextRequest>(request => 
            {
                _requestCounter++;
                Console.WriteLine($"RequestManager: Received request #{_requestCounter} for SessionId '{request.SessionId}' '{request.Text.Substring(0, Math.Min(request.Text.Length, 20))}...'. Creating ChatAgent.");
                
                var chatAgentWorker = Context.ActorOf<ChatAgent>();
                
                // Forward the entire ProcessTextRequest (which includes Text and SessionId) to the worker
                chatAgentWorker.Tell(request, Self); 
            });
        }

        protected override void PreStart()
        {
            Console.WriteLine("RequestManagerActor started.");
        }

        protected override void PostStop()
        {
            Console.WriteLine("RequestManagerActor stopped.");
        }
    }
} 