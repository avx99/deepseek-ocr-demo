#!/bin/bash

# DeepSeek OCR Docker Entrypoint Script

set -e

echo "Starting DeepSeek OCR..."

# Create necessary directories
mkdir -p /app/uploads /app/results /app/logs /app/models

# Set permissions
chmod 755 /app/uploads /app/results /app/logs /app/models

# Copy environment file if it doesn't exist
if [ ! -f /app/.env ]; then
    if [ -f /app/.env.example ]; then
        cp /app/.env.example /app/.env
        echo "Created .env file from example"
    fi
fi

# Check for CUDA availability
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
else
    echo "No NVIDIA GPU detected, using CPU"
    export DEVICE=cpu
fi

# Check if model files exist
if [ "$USE_LOCAL_MODEL" = "true" ]; then
    MODEL_PATH="/app/models/deepseek-vl-7b-chat"
    if [ ! -d "$MODEL_PATH" ]; then
        echo "Warning: Local model not found at $MODEL_PATH"
        echo "Please download the model or use API mode"
        echo "To download the model, run:"
        echo "git clone https://huggingface.co/deepseek-ai/deepseek-vl-7b-chat $MODEL_PATH"
    else
        echo "Local model found at $MODEL_PATH"
    fi
fi

# Install any missing packages
if [ -f /app/requirements.txt ]; then
    pip install --no-cache-dir -r /app/requirements.txt
fi

# Run database migrations or setup if needed
# (Add any initialization scripts here)

# Start the application
echo "Starting Flask application..."
cd /app

# Choose the startup method based on environment
if [ "$FLASK_ENV" = "development" ]; then
    python3 -m app.main
else
    # Production mode with gunicorn
    if command -v gunicorn &> /dev/null; then
        exec gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 app.main:create_app()
    else
        exec python3 -m app.main
    fi
fi