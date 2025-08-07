import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from functools import partial

# Initialize the FastAPI app
app = FastAPI()
logger = logging.getLogger('uvicorn')

# Define the paths to the configuration files
# The paths are relative to the project's root directory.
CONFIG_FILE = Path("config.json")
FALLBACK_CONFIG_FILE = Path("app/fallback.json")
STATIC_DIR = Path("static")

# Global variable for the application's configuration
app_config = {}

# --- Route Handlers ---
# These functions will be dynamically assigned to the endpoints
def get_config_handler():
    """Returns the current application configuration."""
    return app_config

def get_stats_handler():
    """Returns static data for the stats endpoint from the config."""
    return app_config.get("api", {}).get("endpoints", {}).get("stats", {}).get("data", {"message": "Stats not available"})

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
    
    # Loop through all defined endpoints and create a route for each
    for endpoint_name, endpoint_details in endpoints.items():
        route_path = f"{api_base_path}{endpoint_details['path']}"
        handler_name = endpoint_details.get("handler")
        
        if handler_name == "get_config_handler":
            logger.info(f"Creating dynamic route for '{endpoint_name}' at '{route_path}' using handler: {handler_name}")
            app.get(route_path)(get_config_handler)
        elif handler_name == "get_stats_handler":
            logger.info(f"Creating dynamic route for '{endpoint_name}' at '{route_path}' using handler: {handler_name}")
            app.get(route_path)(get_stats_handler)
        elif "data" in endpoint_details:
            logger.info(f"Creating dynamic route for '{endpoint_name}' at '{route_path}' with static data.")
            data = endpoint_details.get("data")
            app.get(route_path)(create_static_data_handler(data))
        else:
            logger.warning(f"Skipping endpoint '{endpoint_name}': No valid handler or data defined.")

# --- Configuration Loading ---
def load_config():
    global app_config
    hardcoded_fallback = {
        "server": {
            "host": "127.0.0.1",
            "port": 8080,
            "debug": True,
            "log_level": "debug"
        },
        "api": {
            "version": "v1",
            "base_path": "/api",
            "endpoints": {
                "config": { "path": "/config", "handler": "get_config_handler" },
                "stats": { "path": "/stats", "handler": "get_stats_handler", "data": { "total_users": 0, "active_sessions": 0, "message": "hardcoded fallback values" } }
            }
        },
        "features": {
            "enable_dashboard": False,
            "enable_terminal": False
        }
    }
    
    try:
        logger.info(f"Loading configuration from {CONFIG_FILE.resolve()}")
        with open(CONFIG_FILE, "r") as f:
            app_config = json.load(f)
        logger.info("Configuration loaded successfully.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Error loading {CONFIG_FILE}. Attempting to load fallback configuration...")
        logger.warning(f"Error message: {e}")
        try:
            with open(FALLBACK_CONFIG_FILE, "r") as f:
                app_config = json.load(f)
            logger.info("Fallback configuration loaded successfully.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error: {FALLBACK_CONFIG_FILE} not found or is invalid.")
            logger.info("Using internally defined fallback values.")
            app_config = hardcoded_fallback

# --- Main Application Logic ---
# Load the configuration when the application starts
load_config()

# Setup all dynamic API routes based on the loaded configuration
setup_dynamic_routes()

# API endpoint for the main page
@app.get("/")
async def get_index():
    """Serves the main index.html file."""
    logger.debug('Serves the main file.')
    return FileResponse("index.html")

# Serve static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Programmatically start the Uvicorn server
if __name__ == "__main__":
    server_host = app_config.get("server", {}).get("host", "127.0.0.1")
    server_port = app_config.get("server", {}).get("port", 8080) # Using 8080 as a default
    server_reload = app_config.get("server", {}).get("debug", False)
    log_level = app_config.get("server", {}).get("log_level", "info")
    
    logger.info(f"Starting server on http://{server_host}:{server_port} with reload={server_reload} and log level={log_level}")
    
    uvicorn.run(
        "main:app",
        host=server_host, 
        port=server_port, 
        reload=server_reload,
        log_level=log_level
    )