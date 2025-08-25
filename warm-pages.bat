# Maritime Assistant Performance Optimization Script
# This script pre-warms all Next.js pages to avoid first-load delays

echo "🚢 Pre-warming Maritime Assistant pages..."

# Wait for server to be ready
timeout /t 3 /nobreak > nul

# Pre-compile all pages
echo "Warming up Chat Assistant..."
curl -s http://localhost:3000/chat > nul

echo "Warming up Document Analysis..."
curl -s http://localhost:3000/documents > nul

echo "Warming up Weather & Distance..."
curl -s http://localhost:3000/weather > nul

echo "Warming up Recommendations..."
curl -s http://localhost:3000/recommendations > nul

echo "Warming up Settings..."
curl -s http://localhost:3000/settings > nul

echo "✅ All pages pre-compiled and ready!"
echo "🌐 Access your Maritime Assistant at: http://localhost:3000"
