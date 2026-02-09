#!/bin/bash
# Auto-deploy script - Just provide your GitHub repo URL

echo "GitHub Auto-Deploy for AI Sourcing Agent"
echo "========================================="
echo ""

# Check if git is configured
if ! git config user.name > /dev/null 2>&1; then
    echo "Setting up git config..."
    git config user.name "Avinash"
    git config user.email "avinash@frameai.com"
fi

echo "✓ Git configured"
echo ""
echo "Please create a GitHub repo first:"
echo "  1. Go to: https://github.com/new"
echo "  2. Name: ai-sourcing-agent"
echo "  3. Make it PUBLIC (required for free Actions)"
echo "  4. Don't add README or .gitignore"
echo "  5. Click 'Create repository'"
echo ""
read -p "Enter your GitHub repo URL (e.g., https://github.com/username/ai-sourcing-agent.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "Error: No URL provided"
    exit 1
fi

echo ""
echo "Pushing to GitHub..."

cd /home/kali/ai_agents_learning

# Add remote
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

# Rename branch to main
git branch -M main

# Push
git push -u origin main

echo ""
echo "✅ DONE! Your code is on GitHub!"
echo ""
echo "Final step:"
echo "  1. Go to: ${REPO_URL%.git}"
echo "  2. Click 'Actions' tab"
echo "  3. Click 'I understand my workflows, go ahead and enable them'"
echo ""
echo "That's it! Agent will run daily at 9 AM UTC automatically."
echo ""
