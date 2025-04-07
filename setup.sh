#!/bin/bash

# Setup script for Databricks Gateway
# This script helps create the .env file with the necessary configuration

echo "Databricks Gateway Setup"
echo "======================="
echo "This script will help you set up your .env file for the Databricks Gateway."
echo ""

# Check if .env already exists
if [ -f .env ]; then
    read -p ".env file already exists. Do you want to overwrite it? (y/n): " overwrite
    if [[ $overwrite != "y" && $overwrite != "Y" ]]; then
        echo "Setup cancelled. Your existing .env file was not modified."
        exit 0
    fi
fi

# Get Databricks token
read -p "Enter your Databricks API token: " databricks_token

# Get Databricks base URL (with default)
default_url="<YOUR_DATABRICKS_BASE_URL>"
read -p "Enter your Databricks base URL [$default_url]: " databricks_base_url
databricks_base_url=${databricks_base_url:-$default_url}

# Get available models (with default)
default_model="databricks-meta-llama-3-1-405b-instruct"
read -p "Enter comma-separated list of available models [$default_model]: " available_models
available_models=${available_models:-$default_model}

# Get port (with default)
default_port="5000"
read -p "Enter the port to run the server on [$default_port]: " port
port=${port:-$default_port}

# Get debug mode (with default)
default_debug="False"
read -p "Enable debug mode? (True/False) [$default_debug]: " debug
debug=${debug:-$default_debug}

# Create .env file
cat > .env << EOL
# Databricks API Configuration
DATABRICKS_TOKEN=${databricks_token}
DATABRICKS_BASE_URL=${databricks_base_url}

# Available models (comma-separated list)
AVAILABLE_MODELS=${available_models}

# Server Configuration
PORT=${port}
DEBUG=${debug}
EOL

echo ""
echo ".env file created successfully!"
echo ""
echo "To start the server, run:"
echo "  python app.py"
echo ""
echo "Or using Docker:"
echo "  docker build -t databricks-gateway ."
echo "  docker run -p ${port}:${port} --env-file .env databricks-gateway"
echo ""
echo "To test the API, run:"
echo "  python test_api.py"
echo ""