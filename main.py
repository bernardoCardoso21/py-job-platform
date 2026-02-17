import webbrowser
import time
import subprocess
import sys

def main():
    print("--- Async Job Platform Launcher ---")
    
    # 1. Start Docker services
    print("Starting Docker containers...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
    except Exception as e:
        print(f"Error starting Docker: {e}")
        sys.exit(1)

    # 2. Open Swagger UI in browser
    url = "http://localhost:8000/docs"
    print(f"Opening Swagger UI at {url}...")
    
    # Give the API a second to warm up if it was just started
    time.sleep(2) 
    webbrowser.open(url)
    
    print("\nSystem is running!")
    print("Press Ctrl+C to stop services (if running in foreground) or just close this window.")
    print("Note: Containers will keep running in the background.")

if __name__ == "__main__":
    main()
