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
            var scriptName = "script.py";
            var scriptPath = Path.Combine(AppContext.BaseDirectory, scriptName); 
            var workspaceRoot = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
            var venvSitePackages = Path.Combine(workspaceRoot, ".venv", "lib", "python3.13", "site-packages");
                                                                     
            if (!PythonEngine.IsInitialized)
            {
                // User sets PYTHONNET_PYDLL and PYTHONHOME in shell
                Console.WriteLine("Attempting to initialize PythonEngine. Ensure PYTHONNET_PYDLL and PYTHONHOME are set correctly in your shell.");
                PythonEngine.Initialize();
                PythonEngine.BeginAllowThreads();
            }

            if (!File.Exists(scriptPath))
            {
                Console.WriteLine($"Error: Python script '{scriptName}' not found at {scriptPath}. ChatAgent will not process messages via Python.");
            }
            else
            {
                try
                {
                    using (Py.GIL()) 
                    {
                        dynamic sys = Py.Import("sys");
                        Console.WriteLine($"Python sys.executable before sys.path append: {sys.executable}");
                        Console.WriteLine($"Python sys.prefix before sys.path append: {sys.prefix}");
                        Console.WriteLine($"Python sys.path before sys.path append: {sys.path}");

                        string scriptDir = AppContext.BaseDirectory;
                        bool scriptDirInPath = false;
                        foreach (PyObject p in sys.path) {
                            if (p.ToString() == scriptDir) {
                                scriptDirInPath = true;
                                break;
                            }
                        }
                        if (!scriptDirInPath) {
                            sys.path.append(scriptDir);
                            Console.WriteLine($"Appended to sys.path: {scriptDir}");
                        }
                        
                        if (Directory.Exists(venvSitePackages)) 
                        {
                            bool venvSiteInPath = false;
                            foreach (PyObject p in sys.path) {
                                if (p.ToString() == venvSitePackages) {
                                    venvSiteInPath = true;
                                    break;
                                }
                            }
                            if (!venvSiteInPath) {
                                sys.path.append(venvSitePackages);
                                Console.WriteLine($"Appended to sys.path: {venvSitePackages}");
                            }
                        }
                        else {
                            Console.WriteLine($"Warning: venv site-packages directory not found for sys.path append: {venvSitePackages}");
                        }
                        
                        Console.WriteLine($"Python sys.path after sys.path append: {sys.path}");
                        
                        _pythonScript = Py.Import(Path.GetFileNameWithoutExtension(scriptName));
                        Console.WriteLine($"Successfully imported Python script: {scriptName}");
                    }
                }
                catch (PythonException ex)
                {
                    Console.WriteLine($"PythonException during script import in ChatAgent: {ex.Message}");
                    Console.WriteLine($"Python StackTrace: {ex.StackTrace}");
                    if (ex.InnerException != null) Console.WriteLine($"Inner Exception: {ex.InnerException.Message}");
                    try {
                        using(Py.GIL()){
                             dynamic sys = Py.Import("sys");
                             Console.WriteLine($"Python sys.executable on error: {sys.executable}");
                             Console.WriteLine($"Python sys.prefix on error: {sys.prefix}");
                             Console.WriteLine($"Python sys.path on error: {sys.path}");
                        }
                    } catch {}
                }
                catch (Exception ex)
                {
                     Console.WriteLine($"Generic Exception during script import in ChatAgent: {ex.Message}");
                }
            }

            Receive<string>(message =>
            {
                if (_pythonScript == null)
                {
                    Console.WriteLine($"ChatAgent cannot process message: Python script was not loaded successfully.");
                    return;
                }
                string response = "Error processing message with Python.";
                try
                {
                    using (Py.GIL()) 
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
                     if (ex.InnerException != null) Console.WriteLine($"Inner Exception: {ex.InnerException.Message}");
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
            base.PostStop();
            Console.WriteLine("ChatAgent stopped.");
        }
    }
} 