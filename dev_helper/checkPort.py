import psutil

# List all processes and check for subprocesses related to your workers
for proc in psutil.process_iter(['pid', 'name', 'status']):
    try:
        # Access process information
        pid = proc.info.get('pid')
        name = proc.info.get('name')
        status = proc.info.get('status')
        print(f"PID: {pid}, Name: {name}, Status: {status}")

        # Now check for connections separately
        connections = proc.connections(kind='inet')  # Use kind='inet' to get internet connections
        if connections:
            for conn in connections:
                # Check if there's a local address (port)
                if conn.laddr:
                    print(f"  - Port: {conn.laddr.port}, Status: {conn.status}")

    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        # Handle cases where the process has been terminated or is inaccessible
        print(f"Could not access process {proc}: {str(e)}")
