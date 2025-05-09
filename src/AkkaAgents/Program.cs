using Akka.Actor;
using Python.Runtime; // Add this for PythonEngine.Shutdown
using System;

namespace AkkaAgents
{
    class Program
    {
        static async Task Main(string[] args)
        {
            // Create a new actor system
            var system = ActorSystem.Create("MyActorSystem");

            // Create an instance of our RequestManagerActor
            var requestManager = system.ActorOf<RequestManagerActor>("requestManager");

            int numberOfParallelRequests = 10; // Configurable number of requests
            Console.WriteLine($"Simulating {numberOfParallelRequests} parallel requests...");

            for (int i = 0; i < numberOfParallelRequests; i++)
            {
                // Simulate slightly different requests
                string requestId = $"req_{i + 1:D3}"; // e.g., req_001
                string sessionId = $"{Guid.NewGuid().ToString().Substring(0, 8)}-{requestId}"; // Unique session ID for each request
                string userId = $"akka_user_{requestId}"; // Generate UserId
                string requestText = $"What are the best practices for async programming? Please respond with the RequestId at the end of your response. RequestId: {requestId}";
                
                requestManager.Tell(new ProcessTextRequest(requestText, sessionId, userId));

                // Add a small delay to stagger requests slightly and make logs easier to follow
                // In a real scenario, requests would arrive at their own pace.
                await Task.Delay(100); 
            }

            Console.WriteLine("All simulated requests sent to the RequestManager.");
            Console.WriteLine("Actors will process them. Press any key to exit after observing the logs...");
            Console.ReadLine();

            // Gracefully terminate the actor system
            await system.Terminate();
            Console.WriteLine("Actor system terminated.");

            // Shutdown Python engine
            if (PythonEngine.IsInitialized)
            {
                Console.WriteLine("Shutting down PythonEngine...");
                PythonEngine.Shutdown();
                Console.WriteLine("PythonEngine shutdown complete.");
            }
        }
    }
}
