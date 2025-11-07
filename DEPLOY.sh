#!/bin/bash
# Deployment script for Doctor Link Tracker

set -e

echo "🚀 Doctor Link Tracker - Deployment Script"
echo "==========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo ""
    echo "Creating .env from template..."
    
    if [ -f env.template ]; then
        cp env.template .env
        echo "✅ .env file created"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env file with your Telegram credentials:"
        echo "   nano .env"
        echo ""
        echo "You need to set:"
        echo "  - TELEGRAM_BOT_TOKEN (get from @BotFather)"
        echo "  - TELEGRAM_CHAT_ID (get from @userinfobot)"
        echo ""
        read -p "Press Enter after you've edited .env file..."
    else
        echo "❌ env.template not found"
        exit 1
    fi
else
    echo "✅ .env file exists"
fi

# Create data directory
echo ""
echo "Creating data directory..."
mkdir -p data
echo "✅ Data directory created"

# Build and start services
echo ""
echo "Building Docker images..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 5

# Check health
echo ""
echo "Checking service health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Service is healthy!"
else
    echo "⚠️  Service might still be starting up..."
    echo "   Check logs: docker-compose logs -f"
fi

echo ""
echo "==========================================="
echo "🎉 Deployment complete!"
echo ""
echo "Service URL: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
echo ""
echo "Next steps:"
echo "  1. Create a link:"
echo "     docker-compose exec web uv run python -m src.cli create test https://google.com"
echo ""
echo "  2. View all links:"
echo "     docker-compose exec web uv run python -m src.cli list"
echo ""
echo "  3. Send test report:"
echo "     docker-compose exec scheduler uv run python -m src.cli send-report daily"
echo ""
echo "  4. View logs:"
echo "     docker-compose logs -f"
echo ""
echo "For more commands, see README.md or run: make help"
echo ""
