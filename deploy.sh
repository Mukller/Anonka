#!/bin/bash

echo "🚀 Starting Anonka bot deployment..."

mkdir -p /home/anton/anonka
cd /home/anton/anonka

if [ -d ".git" ]; then
    echo "📦 Updating repository..."
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone https://github.com/Mukller/Anonka.git .
fi

if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📚 Installing dependencies..."
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "⚠️ Please edit .env file with your configuration"
fi

echo "🗄️ Initializing database..."
cd backend
python init_db.py

echo "✅ Deployment completed!"
