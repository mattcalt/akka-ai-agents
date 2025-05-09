using Akka.Actor;
using AkkaAgents; // Add this to reference our actor's namespace
using System;
using Python.Runtime; // Add this for PythonEngine.Shutdown

namespace AkkaAgents
{
    class Program
    {
        static void Main(string[] args)
        {
            // Create a new actor system
            var system = ActorSystem.Create("MyActorSystem");

            // Create an instance of our ChatAgent
            var chatAgent = system.ActorOf<ChatAgent>("chatAgent");
            chatAgent.Tell("What tools do you have access to?");

            // Keep the system alive until a key is pressed
            Console.WriteLine("Press any key to exit...");
            Console.ReadLine();

            // Terminate the actor system
            system.Terminate().Wait();

            // Shutdown Python engine
            if (PythonEngine.IsInitialized)
            {
                PythonEngine.Shutdown();
            }
        }
    }
}
