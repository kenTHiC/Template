# Dynamic FastAPI Project

This is a dynamic web project built with FastAPI, HTML5, and JavaScript. The structure of the website and the API endpoints can be fully configured using JSON files.

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.10 or newer installed.

### Installation

1.  Clone this repository:
    ```bash
    git clone [Your Repository URL]
    cd [Your Project Name]
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Server

Navigate to the project's root directory and start the server with the following command:

```bash
python app/main.py
```
The server will start on the host and port defined in your `config.json`, with `http://127.0.0.1:5500` as the default.

## ⚙️ Configuration

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

## 📝 License
This project is licensed under the CC0-1.0 License. See the [LICENSE](LICENSE.md) file for more details.