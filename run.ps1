# Set the environment variable for Python's breakpoint
$env:PYTHONBREAKPOINT = "ipdb.set_trace"

# Run the Python script with ipython
uv run ipython main.py
