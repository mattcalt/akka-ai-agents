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

                    // 1. Append script's own directory to sys.path
                    // This ensures the script itself can be imported if it's not in Python's CWD.
                    string scriptDir = AppContext.BaseDirectory;
                    bool scriptDirInPath = false;
                    foreach (PyObject p in sys.path) {
                        if (p.ToString() == scriptDir) { scriptDirInPath = true; break; }
                    }
                    if (!scriptDirInPath) {
                        sys.path.append(new PyString(scriptDir)); // Use PyString for clarity
                    }

                    // 2. Append venv site-packages to sys.path for dependencies
                    if (Directory.Exists(venvSitePackages))
                    {
                        bool venvSiteInPath = false;
                        foreach (PyObject p in sys.path) {
                            if (p.ToString() == venvSitePackages) { venvSiteInPath = true; break; }
                        }
                        if (!venvSiteInPath) {
                            sys.path.append(new PyString(venvSitePackages));
                        }
                    }
                    else
                    {
                        Console.WriteLine($"PythonScriptExecutor: Warning - venv site-packages directory not found for script '{_moduleName}': {venvSitePackages}");
                    }
                    
                    _pythonModule = Py.Import(_moduleName); // Import by module name (e.g., "script")
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
                        // Convert C# arguments to PyObject using ToPython()
                        pyArgs[i] = args[i].ToPython();
                    }

                    dynamic result = _pythonModule!.InvokeMethod(functionName, pyArgs);
                    return result?.ToString(); // Convert result back to C# string
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