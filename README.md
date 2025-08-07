# Dynamic FastAPI Project

This is a dynamic web project built with FastAPI, HTML5, and JavaScript. The structure of the website and the API endpoints can be fully configured using JSON files.

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.10 or newer installed.

### Installation

1.  Clone this repository:
    ```bash
    git clone https://github.com/kenthic/template.git
    cd template
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Server

Navigate to the project's root directory and start the server with the following command. The server will use the host and port defined in your `config.json` by default.

```bash
# Start server with default configuration
python app/main.py

# Override server host and port
python app/main.py -s 0.0.0.0 -p 5021

# Load a custom API configuration file
python app/main.py -c custom-api.json
```

---

## ⚙️ Configuration

Server settings and API endpoints are controlled by `config.json`. If this file is not found, the server will fall back to `app/fallback.json`.

**Application Metadata (`app.json`)**

For the website title, metadata, and project information, the application uses `app.json`. If this file does not exist, the server will use fallback values.

To create `app.json` easily, use the guided assistant:
```bash
python app/main.py --init
```

API endpoints and server settings are controlled by `config.json`. If this file is not found or is invalid, the server will fall back to `app/fallback.json`.

**Customizing the Configuration**

Open `config.json` to modify API routes, port settings, and features.

Example for an endpoint:
```json
"endpoints": {
  "config": {
    "path": "/config", 
    "handler": "get_config_handler"
  }
}
```

or use a custom API config by using a custom `custom-api.json`.
```json
  "api": {
    "version": "v1",
    "base_path": "/api",
    "endpoints": {
      "ping": {
        "path": "/ping",
        "handler": "no_handler",
        "data": { "status": "pong!" }
      }
    }
  }
```

## 📝 License
This project is licensed under the CC0-1.0 License. See the [LICENSE](LICENSE.md) file for more details.