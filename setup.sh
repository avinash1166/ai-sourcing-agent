#!/bin/bash
# Quick Setup Script for AI Sourcing Agent
# Run this first to set up everything

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          AI Sourcing Agent - Setup Script                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if Ollama is installed
echo ""
echo "Checking for Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "✗ Ollama not found."
    echo ""
    echo "Install Ollama? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo "Please install Ollama manually: https://ollama.com"
        exit 1
    fi
fi

echo "✓ Ollama found"

# Check if Ollama is running
echo ""
echo "Checking Ollama service..."
if ! ollama list &> /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 3
fi

# Pull the lightweight model
echo ""
echo "Checking for qwen2.5:3b model..."
if ! ollama list | grep -q "qwen2.5:3b"; then
    echo "Pulling qwen2.5:3b model (1.9GB)..."
    echo "This may take a few minutes depending on your connection..."
    ollama pull qwen2.5:3b
else
    echo "✓ qwen2.5:3b model already installed"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install langchain langchain-ollama langgraph python-dotenv --quiet

echo "✓ Core dependencies installed"

# Ask about web scraping
echo ""
echo "Install web scraping dependencies (Playwright)? (~500MB)"
echo "Required for automated vendor discovery from Alibaba/Made-in-China"
echo "You can skip this and run in test mode only. (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Installing Playwright..."
    pip3 install playwright --quiet
    echo "Installing Chromium browser..."
    playwright install chromium
    echo "✓ Web scraping enabled"
else
    echo "⊘ Skipping web scraping (test mode only)"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/logs data/reports
echo "✓ Directories created"

# Make main.py executable
chmod +x main.py 2>/dev/null

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ✓ SETUP COMPLETE                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the system:"
echo "   python3 main.py --test"
echo ""
echo "2. Run full workflow (if Playwright installed):"
echo "   python3 main.py"
echo ""
echo "3. Check the README for more options:"
echo "   cat README.md"
echo ""
echo "4. View generated reports:"
echo "   ls -lh data/reports/"
echo ""
