#!/bin/bash

echo "🔄 Updating GitHub Repository to React Version..."

# Navigate to your existing repo
cd /path/to/your/peer-bank-analytics

# Create backup branch
echo "📦 Creating backup of Streamlit version..."
git checkout -b streamlit-backup
git push origin streamlit-backup

# Switch back to main
git checkout main

# Remove old Streamlit files
echo "🗑️ Removing Streamlit files..."
rm -rf pages/
rm -rf src/
rm -rf images/
rm -rf react-app/
rm -f *.py
rm -f requirements.txt
rm -f .streamlit/

# Copy new React files
echo "📁 Adding React version..."
cp -r /Users/shamakka/Documents/projects/peer-bank-analytics-blog/bankiq-react-app/* .

# Update git
echo "📝 Committing changes..."
git add .
git commit -m "🚀 Major Release: Migrate from Streamlit to React

- Complete rewrite with React + Flask architecture
- Modern Material-UI interface with tabbed navigation  
- Enhanced charts with Recharts
- Mobile responsive design
- One-command startup script
- Professional error handling and loading states
- Updated to 2024-2025 data

BREAKING CHANGE: Streamlit version moved to 'streamlit-backup' branch"

# Push changes
echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Repository updated successfully!"
echo "📊 Your friend can now access the modern React version"
echo "🔗 Streamlit backup available at: streamlit-backup branch"