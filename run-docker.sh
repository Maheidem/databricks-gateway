#!/bin/bash

# Default values
PORT=5000
DEBUG=False

# Help message
show_help() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -t, --token TOKEN       Databricks API token (required)"
  echo "  -u, --url URL           Databricks base URL (required)"
  echo "  -m, --models MODELS     Comma-separated list of models (required)"
  echo "  -p, --port PORT         Port to run the server on (default: 5000)"
  echo "  -d, --debug             Enable debug mode"
  echo "  -h, --help              Show this help message"
  echo ""
  echo "Example:"
  echo "  $0 --token your_token --url <YOUR_DATABRICKS_BASE_URL> --models model1,model2"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -t|--token)
      DATABRICKS_TOKEN="$2"
      shift
      shift
      ;;
    -u|--url)
      DATABRICKS_BASE_URL="$2"
      shift
      shift
      ;;
    -m|--models)
      AVAILABLE_MODELS="$2"
      shift
      shift
      ;;
    -p|--port)
      PORT="$2"
      shift
      shift
      ;;
    -d|--debug)
      DEBUG=True
      shift
      ;;
    -h|--help)
      show_help
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      ;;
  esac
done

# Check required parameters
if [ -z "$DATABRICKS_TOKEN" ] || [ -z "$DATABRICKS_BASE_URL" ] || [ -z "$AVAILABLE_MODELS" ]; then
  echo "Error: Missing required parameters"
  show_help
fi

# Run the Docker container
echo "Starting Databricks Gateway container..."
echo "Base URL: $DATABRICKS_BASE_URL"
echo "Models: $AVAILABLE_MODELS"
echo "Port: $PORT"
echo "Debug mode: $DEBUG"

docker run -p $PORT:$PORT \
  -e DATABRICKS_TOKEN="$DATABRICKS_TOKEN" \
  -e DATABRICKS_BASE_URL="$DATABRICKS_BASE_URL" \
  -e AVAILABLE_MODELS="$AVAILABLE_MODELS" \
  -e PORT="$PORT" \
  -e DEBUG="$DEBUG" \
  databricks-gateway