# Databricks Gateway - OpenAI API Compatibility Wrapper

This project provides a wrapper around Databricks LLM serving endpoints to make them compatible with the OpenAI API format. This allows you to use services that support OpenAI-compatible models with your Databricks-hosted models by providing a custom base URL and API key.

## Features

- **OpenAI API Compatibility**: Implements the essential endpoints required by OpenAI-compatible clients:
  - `GET /v1/models`: Lists available models
  - `POST /v1/chat/completions`: Handles chat completion requests
  - `POST /v1/completions`: Handles standard completion requests
  - `POST /v1/embeddings`: Handles embedding requests (placeholder implementation)

- **Configuration Options**: Easily configure which models to expose and other settings via environment variables

- **Production-Ready**: Includes Docker support for containerized deployment

## Prerequisites

- Python 3.8+
- Databricks account with an LLM serving endpoint
- Databricks API token with access to the serving endpoint

## Installation

### Local Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/databricks_gateway.git
   cd databricks_gateway
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your Databricks API token and other settings:
   ```
   DATABRICKS_TOKEN=your_databricks_token_here
   DATABRICKS_BASE_URL=<YOUR_DATABRICKS_BASE_URL>
   AVAILABLE_MODELS=databricks-meta-llama-3-1-405b-instruct
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t databricks-gateway .
   ```

2. Run the container with environment variables:
   ```bash
   docker run -p 5000:5000 \
     -e DATABRICKS_TOKEN="your_databricks_token_here" \
     -e DATABRICKS_BASE_URL="<YOUR_DATABRICKS_BASE_URL>" \
     -e AVAILABLE_MODELS="databricks-meta-llama-3-1-405b-instruct" \
     databricks-gateway
   ```

   Alternatively, you can use an environment file:
   ```bash
   docker run -p 5000:5000 --env-file .env databricks-gateway
   ```

3. For convenience, you can also use the provided shell script:
   ```bash
   # Make the script executable
   chmod +x run-docker.sh
   
   # Run with required parameters
   ./run-docker.sh --token your_token --url your_databricks_base_url --models model1,model2
   
   # For help and additional options
   ./run-docker.sh --help
   ```


### Docker Compose Setup

For easier management, especially when deploying alongside other services, you can use Docker Compose.

1.  **Prerequisites:** Ensure you have Docker Compose installed (it's usually included with Docker Desktop).

2.  **Configure Environment:** Make sure your `.env` file is correctly configured with your Databricks token, base URL, and desired models as described in the [Local Setup](#local-setup) section.

3.  **Start the Service:**
    ```bash
    docker-compose up -d
    ```
    This command will build the image (if necessary) and start the container in detached mode.

4.  **Stop the Service:**
    ```bash
    docker-compose down
    ```

#### Deployment with Portainer

If you are using Portainer to manage your Docker environment, you can deploy this service as a Stack:

1.  Navigate to **Stacks** in your Portainer interface.
2.  Click **+ Add stack**.
3.  Give the stack a name (e.g., `databricks-gateway`).
4.  Select the **Web editor** as the build method.
5.  Paste the contents of the `docker-compose.yml` file provided in this repository into the editor.
6.  Scroll down to the **Environment variables** section.
7.  Click **+ Add environment variable** for each variable defined in your `.env` file (`DATABRICKS_TOKEN`, `DATABRICKS_BASE_URL`, `AVAILABLE_MODELS`, `PORT` (optional)). Set their corresponding values.
    *Alternatively, if your Portainer version supports it, you might be able to upload the `.env` file directly or use secrets management.*
8.  Click **Deploy the stack**.

Portainer will pull/build the image and deploy the container based on your `docker-compose.yml` and the environment variables you provided.

## Usage

After starting the server, you can use any OpenAI client library to interact with your Databricks models:

### Example with OpenAI Python Client

```python
from openai import OpenAI

# Point to your local server instead of OpenAI
client = OpenAI(
    base_url="http://localhost:5000/v1",
    api_key="not-needed-but-required-by-client"  # The wrapper doesn't use this, but the client requires it
)

# List available models
models = client.models.list()
print(models)

# Chat completion
chat_completion = client.chat.completions.create(
    model="databricks-meta-llama-3-1-405b-instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)
print(chat_completion.choices[0].message.content)

# Text completion
completion = client.completions.create(
    model="databricks-meta-llama-3-1-405b-instruct",
    prompt="Complete this sentence: The quick brown fox"
)
print(completion.choices[0].text)
```

### Example with cURL

```bash
# List models
curl http://localhost:5000/v1/models

# Chat completion
curl http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "databricks-meta-llama-3-1-405b-instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'

# Text completion
curl http://localhost:5000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "databricks-meta-llama-3-1-405b-instruct",
    "prompt": "Complete this sentence: The quick brown fox"
  }'
```

## Configuration Options

All configuration is done through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABRICKS_TOKEN` | Your Databricks API token | (Required) |
| `DATABRICKS_BASE_URL` | Base URL for Databricks API | <YOUR_DATABRICKS_BASE_URL> |
| `AVAILABLE_MODELS` | Comma-separated list of model IDs to expose | databricks-meta-llama-3-1-405b-instruct |
| `PORT` | Port to run the server on | 5000 |
| `DEBUG` | Enable debug mode | False |

## Docker Environment Variables

When running the Docker container, you can pass the required parameters directly:

```bash
docker run -p 5000:5000 \
  -e DATABRICKS_TOKEN="your_databricks_token_here" \
  -e DATABRICKS_BASE_URL="your_databricks_base_url" \
  -e AVAILABLE_MODELS="model1,model2,model3" \
  databricks-gateway
```

This allows you to easily configure the gateway for different Databricks endpoints and models.

## Health Check

The service provides a health check endpoint:

```bash
curl http://localhost:5000/healthcheck
```

## Security Considerations

- This wrapper does not implement authentication itself, as it's designed to run behind a secure gateway or proxy
- In production, consider adding an API key check or other authentication mechanism
- Always run in a secure network environment

## Customization

To add support for more Databricks models or customize the behavior:

1. Edit the `.env` file to add more models to `AVAILABLE_MODELS`
2. For more advanced customization, modify the request/response handling in `app.py`

## Limitations

- The embedding endpoint is a placeholder and needs to be customized based on your specific embedding model
- Error handling might need adjustment based on the specific Databricks model responses
- The wrapper assumes the Databricks endpoint is OpenAI-compatible at the input/output level

## License

[MIT License](LICENSE)