using Akka.Actor;
using System;

namespace AkkaAgents
{
    // Define a message type for requests
    public record ProcessTextRequest(string Text);

    public class RequestManagerActor : ReceiveActor
    {
        private int _requestCounter = 0;

        public RequestManagerActor()
        {
            Receive<ProcessTextRequest>(request =>
            {
                _requestCounter++;
                Console.WriteLine($"RequestManager: Received request #{_requestCounter} '{request.Text.Substring(0, Math.Min(request.Text.Length, 20))}...'. Creating ChatAgent to handle it.");
                
                // Create a new ChatAgent for each request. 
                // Akka.NET automatically assigns unique names to these children (e.g., $a, $b, $c)
                var chatAgentWorker = Context.ActorOf<ChatAgent>();
                
                // Forward the original message text to the worker
                chatAgentWorker.Tell(request.Text, Self); // Pass the original text content
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