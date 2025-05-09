using Python.Runtime;
using System;
using System.IO;

namespace AkkaAgents.Utilities
{
    public class PythonScriptExecutor : IDisposable
    {
        private readonly dynamic? _pythonModule;
        private readonly string _moduleName;

        // Static constructor ensures Python engine is initialized only once per application lifetime.
        static PythonScriptExecutor()
        {
            if (!PythonEngine.IsInitialized)
            {
                // PYTHONNET_PYDLL and PYTHONHOME are expected to be set by the user in their shell.
                Console.WriteLine("PythonScriptExecutor: Initializing PythonEngine. Ensure PYTHONNET_PYDLL and PYTHONHOME are set in your shell.");
                PythonEngine.Initialize();
                PythonEngine.BeginAllowThreads(); // Essential for multi-threaded environments like Akka.NET
            }
        }

        public PythonScriptExecutor(string scriptFileName)
        {
            _moduleName = scriptFileName.Replace(Path.DirectorySeparatorChar, '.').Replace(Path.AltDirectorySeparatorChar, '.');
            if (_moduleName.ToLower().EndsWith(".py")) // Remove .py extension, case-insensitive
            {
                _moduleName = _moduleName.Substring(0, _moduleName.Length - 3);
            }

            string scriptFullPath = Path.Combine(AppContext.BaseDirectory, scriptFileName);

            if (!File.Exists(scriptFullPath))
            {
                Console.WriteLine($"PythonScriptExecutor: Error - Python script '{scriptFileName}' not found at {scriptFullPath}.");
                _pythonModule = null;
                return;
            }

            // Calculate paths for sys.path manipulation
            var workspaceRoot = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
            var venvSitePackages = Path.Combine(workspaceRoot, ".venv", "lib", "python3.13", "site-packages");

            try
            {
                using (Py.GIL()) // Acquire Global Interpreter Lock for Python operations
                {
                    dynamic sys = Py.Import("sys");

                    // Log Python environment details
                    Console.WriteLine($"PythonScriptExecutor: sys.executable: {sys.executable}");
                    Console.WriteLine($"PythonScriptExecutor: sys.prefix: {sys.prefix}");
                    Console.WriteLine($"PythonScriptExecutor: Initial sys.path length: {sys.path.Length()}");
                    // Console.WriteLine("PythonScriptExecutor: Initial sys.path content:");
                    // for (int i = 0; i < sys.path.Length(); i++)
                    // {
                    //     Console.WriteLine($"- sys.path[{i}]: {sys.path[i].ToString()}");
                    // }


                    // 1. Prepend Project Workspace Root to sys.path
                    PyObject pyWorkspaceRoot = new PyString(workspaceRoot);
                    // Remove if it exists anywhere, to avoid duplicates if this code runs multiple times or path is already there
                    try
                    {
                        PyList sysPathList = sys.path.As<PyList>();
                        if (sysPathList.Contains(pyWorkspaceRoot))
                        {
                            sys.path.remove(pyWorkspaceRoot);
                            Console.WriteLine($"PythonScriptExecutor: Removed existing workspace root from sys.path to avoid duplication: {workspaceRoot}");
                        }
                    }
                    catch (PythonException pex) { /* ignore if remove fails, e.g. not found */ 
                        Console.WriteLine($"PythonScriptExecutor: Minor PythonException during pre-emptive remove of workspace root (can be ignored if it was not present): {pex.Message}");
                    }
                    sys.path.insert(0, pyWorkspaceRoot); // Insert at the beginning
                    Console.WriteLine($"PythonScriptExecutor: Prepended workspace root to sys.path: {workspaceRoot}");


                    // 2. Append script's own directory (AppContext.BaseDirectory) to sys.path
                    // This allows Py.Import("Scripts.script") to find ".../bin/Debug/net8.0/Scripts/script.py"
                    string scriptBaseDir = AppContext.BaseDirectory;
                    bool scriptBaseDirInPath = false;
                    foreach (PyObject p in sys.path) {
                        if (p.ToString() == scriptBaseDir) { scriptBaseDirInPath = true; break; }
                    }
                    if (!scriptBaseDirInPath) {
                        sys.path.append(new PyString(scriptBaseDir));
                        Console.WriteLine($"PythonScriptExecutor: Appended script base directory to sys.path: {scriptBaseDir}");
                    }

                    // NEW: 2b. Append the script's container directory in the output (e.g., .../bin/Debug/net8.0/Scripts/)
                    // This helps script.py find sibling packages like 'coordinator_agent'
                    string scriptContainerDir = Path.GetDirectoryName(scriptFullPath)!; // scriptFullPath is like .../bin/Debug/net8.0/Scripts/script.py
                    if (!string.IsNullOrEmpty(scriptContainerDir)) // Basic check
                    {
                        bool scriptContainerDirInPath = false;
                        foreach (PyObject p in sys.path) {
                            if (p.ToString() == scriptContainerDir) { scriptContainerDirInPath = true; break; }
                        }
                        if (!scriptContainerDirInPath) {
                            sys.path.append(new PyString(scriptContainerDir));
                            Console.WriteLine($"PythonScriptExecutor: Appended script container directory to sys.path: {scriptContainerDir}");
                        }
                    }


                    // 3. Append venv site-packages to sys.path for dependencies
                    if (Directory.Exists(venvSitePackages))
                    {
                        bool venvSiteInPath = false;
                        foreach (PyObject p in sys.path) {
                            if (p.ToString() == venvSitePackages) { venvSiteInPath = true; break; }
                        }
                        if (!venvSiteInPath) {
                            sys.path.append(new PyString(venvSitePackages));
                             Console.WriteLine($"PythonScriptExecutor: Appended venv site-packages to sys.path: {venvSitePackages}");
                        }
                    }
                    else
                    {
                        Console.WriteLine($"PythonScriptExecutor: Warning - venv site-packages directory not found for script '{_moduleName}': {venvSitePackages}");
                    }

                    // For debugging, print final sys.path before importing the user script
                    Console.WriteLine("PythonScriptExecutor: Final sys.path content (before importing user module):");
                    PyObject finalSysPath = sys.path;
                    for (int i = 0; i < finalSysPath.Length(); i++)
                    {
                        Console.WriteLine($"- sys.path[{i}]: {finalSysPath[i].ToString()}");
                    }
                    
                    _pythonModule = Py.Import(_moduleName);
                    Console.WriteLine($"PythonScriptExecutor: Successfully imported Python module '{_moduleName}'.");
                }
            }
            catch (PythonException ex)
            {
                Console.WriteLine($"PythonScriptExecutor: PythonException during import of module '{_moduleName}': {ex.Message}");
                Console.WriteLine($"PythonScriptExecutor: Python StackTrace for '{_moduleName}': {ex.StackTrace}");
                if (ex.InnerException != null) Console.WriteLine($"PythonScriptExecutor: Inner Exception: {ex.InnerException.Message}");
                _pythonModule = null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"PythonScriptExecutor: Generic Exception during import of module '{_moduleName}': {ex.Message}");
                _pythonModule = null;
            }
        }

        public bool IsScriptLoaded => _pythonModule != null;

        public string? ExecuteFunction(string functionName, params object[] args)
        {
            if (!IsScriptLoaded)
            {
                Console.WriteLine($"PythonScriptExecutor: Cannot execute function '{functionName}'. Python module '{_moduleName}' is not loaded.");
                return null; 
            }

            try
            {
                using (Py.GIL())
                {
                    var pyArgs = new PyObject[args.Length];
                    for (int i = 0; i < args.Length; i++)
                    {
                        pyArgs[i] = args[i].ToPython();
                    }

                    // Invoke the method to get the initial result
                    dynamic returnedValue = _pythonModule!.InvokeMethod(functionName, pyArgs);

                    // Check if the result is awaitable (e.g., a coroutine)
                    dynamic inspect = Py.Import("inspect");
                    dynamic asyncio = Py.Import("asyncio");

                    if (inspect.isawaitable(returnedValue).As<bool>())
                    {
                        Console.WriteLine($"PythonScriptExecutor: Result of '{_moduleName}.{functionName}' is awaitable. Running with asyncio event loop.");
                        PyObject resultCoroutine = returnedValue; // The returnedValue is the coroutine object
                        dynamic loop;
                        try
                        {
                            // Try to get the currently running event loop
                            loop = asyncio.get_running_loop();
                            Console.WriteLine($"PythonScriptExecutor: Using existing asyncio event loop: {loop}");
                        }
                        catch (PythonException exLoopNotRunning) // Catches RuntimeError if no loop is running
                        {
                            // No current running loop. Create a new one and set it for the current thread.
                            Console.WriteLine($"PythonScriptExecutor: No running asyncio event loop found (Details: {exLoopNotRunning.Message}). Creating and setting a new one.");
                            loop = asyncio.new_event_loop();
                            asyncio.set_event_loop(loop);
                            Console.WriteLine($"PythonScriptExecutor: New event loop created and set: {loop}");
                        }

                        // Ensure the loop is not closed before using it
                        if (loop.is_closed().As<bool>())
                        {
                            Console.WriteLine($"PythonScriptExecutor: Warning - event loop was (or became) closed. Creating and setting a new one for this call.");
                            loop = asyncio.new_event_loop();
                            asyncio.set_event_loop(loop);
                            Console.WriteLine($"PythonScriptExecutor: Re-created and set new event loop after finding it closed: {loop}");
                        }
                        
                        // Run the coroutine to completion
                        dynamic finalResult = loop.run_until_complete(resultCoroutine);
                        Console.WriteLine($"PythonScriptExecutor: Coroutine '{_moduleName}.{functionName}' completed.");
                        return finalResult?.ToString();
                    }
                    else
                    {
                        Console.WriteLine($"PythonScriptExecutor: Result of '{_moduleName}.{functionName}' is not awaitable. Returning directly.");
                        return returnedValue?.ToString(); // Convert result back to C# string
                    }
                }
            }
            catch (PythonException ex)
            {
                Console.WriteLine($"PythonScriptExecutor: PythonException in module '{_moduleName}' function '{functionName}': {ex.Message}");
                Console.WriteLine($"PythonScriptExecutor: Python StackTrace: {ex.StackTrace}");
                if (ex.InnerException != null) Console.WriteLine($"PythonScriptExecutor: Inner Exception: {ex.InnerException.Message}");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"PythonScriptExecutor: Generic Exception in module '{_moduleName}' function '{functionName}': {ex.Message}");
                return null;
            }
        }
        
        public void Dispose()
        {
            // Pythonnet's PyObjects are generally managed by its GC linked to Python's GC.
            // Explicit disposal of _pythonModule (e.g., _pythonModule?.Dispose()) is often not needed
            // unless it represents something like a file handle within Python that needs explicit closing.
            // For a simple module object, this can usually be a no-op.
            // The PythonEngine itself is shutdown globally when the application exits (if configured to do so).
        }
    }
} 