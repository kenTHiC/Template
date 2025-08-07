import json
import argparse
from pathlib import Path
import sys
import logging
from functools import partial
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Initialize the FastAPI app
app = FastAPI()
logger = logging.getLogger('uvicorn.error')

# Define the paths to the configuration files
APP_INFO_FILE = Path("app.json")
CONFIG_FILE = Path("config.json")
FALLBACK_CONFIG_FILE = Path("app/fallback.json")
STATIC_DIR = Path("static")

# Global variables for the application's configuration and info
app_config = {}
app_info = {}

# --- Route Handlers ---
def get_config_handler():
    """Returns the current application configuration."""
    return app_config

def create_static_data_handler(data):
    """
    A helper function to create a handler that returns static data.
    This solves the Python closure issue.
    """
    def handler():
        return data
    return handler

# --- Dynamic Route Setup ---
def setup_dynamic_routes():
    """
    Dynamically creates API routes based on the configuration file.
    """
    global app_config
    
    api_config = app_config.get("api", {})
    api_base_path = api_config.get("base_path", "")
    endpoints = api_config.get("endpoints", {})
    
    for endpoint_name, endpoint_details in endpoints.items():
        if isinstance(endpoint_details, dict):
            route_path = f"{api_base_path}{endpoint_details.get('path', '')}"
            handler_name = endpoint_details.get("handler")
            
            if handler_name == "get_config_handler":
                logger.info(f"Creating dynamic route for '{endpoint_name}' at '{route_path}' using handler: {handler_name}")
                app.get(route_path)(get_config_handler)
            elif "data" in endpoint_details:
                logger.info(f"Creating dynamic route for '{endpoint_name}' at '{route_path}' with static data.")
                data = endpoint_details.get("data")
                app.get(route_path)(create_static_data_handler(data))
            else:
                logger.warning(f"Skipping endpoint '{endpoint_name}': No valid handler or data defined.")
        else:
            logger.warning(f"Skipping endpoint '{endpoint_name}': Invalid endpoint details format.")

# --- Configuration Loading ---
def load_app_info():
    """Loads application metadata from app.json."""
    global app_info
    try:
        logger.info(f"Loading application info from {APP_INFO_FILE.resolve()}")
        with open(APP_INFO_FILE, "r") as f:
            app_info = json.load(f)
        logger.info("Application info loaded successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading {APP_INFO_FILE}: {e}")
        logger.warning("Using fallback values for app info.\nUse 'python app/main.py --init' to create the file.")
        app_info = {
            "info": {"name": "Template-App", "version": {"major": 1,"minor": 0,"patch": 0}},
            "website": {"title": "Default Title", "meta_description": "Default Description", "meta_keywords": []}
        }
    
    app.title = app_info.get('website', {}).get('title', 'Default Title')
    app.description = app_info.get('website', {}).get('meta_description', 'Default Description')

def load_config(config_path: Path = None):
    global app_config
    hardcoded_fallback = {
        "server": { "host": "127.0.0.1", "port": 8080, "debug": False, "log_level": "debug" },
        "api": {
            "version": "v1", "base_path": "/api",
            "endpoints": {
                "config": { "path": "/config", "handler": "get_config_handler" },
                "stats": { "path": "/stats", "data": { "total_users": 100, "active_sessions": 25 } }
            }
        },
        "features": { "enable_dashboard": False, "enable_terminal": False }
    }
    
    # 1. Zuerst die Standard-Konfiguration (oder Fallback) laden
    temp_config = {}
    try:
        with open(CONFIG_FILE, "r") as f:
            temp_config = json.load(f)
        logger.info("Standard configuration loaded successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Error loading {CONFIG_FILE}. Attempting to load fallback configuration...")
        try:
            with open(FALLBACK_CONFIG_FILE, "r") as f:
                temp_config = json.load(f)
            logger.info("Fallback configuration loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error: {FALLBACK_CONFIG_FILE} not found or is invalid. Using fallback.")
            temp_config = hardcoded_fallback

    app_config = hardcoded_fallback.copy()
    if temp_config:
        app_config["server"].update(temp_config.get("server", {}))
        app_config["api"].update(temp_config.get("api", {}))
        app_config["features"].update(temp_config.get("features", {}))
        
    # 2. Dann die benutzerdefinierte Konfiguration (aus -c) laden und nur die API überschreiben
    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                custom_config = json.load(f)
            if custom_config.get("api"):
                app_config["api"].update(custom_config["api"])
                logger.info(f"Custom API configuration from {config_path} applied.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading custom config {config_path}: {e}")

# --- Interactive CLI Helper ---
def initialize_app_json():
    """Interactive assistant to create a new app.json file."""
    print("\n--- App.json Initialization Wizard ---")
    print("Please answer the following questions to create an 'app.json'.")
    
    info = {}
    info["name"] = input("Project name (e.g. 'My Cool App'): ")
    info["author"] = {"name": input("Your name: ")}
    info["version"] = {"major": 1, "minor": 0, "patch": 0}
    info["description"] = input("A brief description of the project: ")
    info["license"] = input("License (e.g. 'MIT' or 'CC0-1.0'): ")
    info["repository"] = {"url": input("Repository URL: ")}

    website = {}
    website["title"] = input("Title for the website: ")
    website["meta_description"] = input("Meta description for SEO: ")
    website["meta_keywords"] = input("Keywords (comma separated): ").split(',')

    new_app_json = {"info": info, "website": website}
    
    try:
        with open(APP_INFO_FILE, "w") as f:
            json.dump(new_app_json, f, indent=2)
        print(f"\napp.json successfully created under '{APP_INFO_FILE.resolve()}'!")
    except IOError as e:
        print(f"\nError writing file: {e}")
        
    sys.exit(0)

# --- Main Application Logic ---
# Register the index.html endpoint
@app.get("/")
async def get_index():
    """Serves the main index.html file."""
    return FileResponse("index.html")

# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# This block runs ONLY when you execute the script directly, e.g., with 'python app/main.py'
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a dynamic FastAPI server or run a CLI command.", 
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="""
Examples:
  python app/main.py --init                       # Start an interactive assistant to create app.json
  python app/main.py -s 0.0.0.0 -p 5021           # Override host and port from the command line
  python app/main.py                              # Start server with host and port from config.json
""")
    parser.add_argument('-s', '--server', dest='host', type=str, help='Override the server host.')
    parser.add_argument('-p', '--port', dest='port', type=int, help='Override the server port.')
    parser.add_argument('-c', '--config', dest='config_file', type=Path, help='Load a custom API configuration file.')
    parser.add_argument('--init', action='store_true', help='Initialize a new app.json file with a guided assistant.')

    args = parser.parse_args()

    # If the --init argument is present, run the assistant and exit
    if args.init:
        initialize_app_json()
    else:
        # Load configurations based on parsed arguments
        load_app_info()
        load_config(config_path=args.config_file)
        setup_dynamic_routes()

        # Get server settings, using command-line arguments if provided
        server_host = args.host if args.host else app_config.get("server", {}).get("host", "127.0.0.1")
        server_port = args.port if args.port else app_config.get("server", {}).get("port", 8080)
        server_reload = app_config.get("server", {}).get("debug", False)
        log_level = app_config.get("server", {}).get("log_level", "info")
        
        logger.info(f"Starting server on http://{server_host}:{server_port}")
        uvicorn.run(app, host=server_host, port=server_port, reload=server_reload, log_level=log_level)