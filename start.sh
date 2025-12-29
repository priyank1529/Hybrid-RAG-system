#!/bin/bash

# Graph RAG Startup Script

echo "🚀 Starting Graph RAG Application..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo "✏️  Please edit .env with your credentials before running again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -e .

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads
mkdir -p data/raw
mkdir -p data/processed

# Run the application
echo "✅ Starting FastAPI server..."
echo "📡 API will be available at: http://localhost:8000"
echo "📖 Documentation at: http://localhost:8000/docs"
echo ""
python main.py
