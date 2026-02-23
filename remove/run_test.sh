#!/bin/bash

# Start API server in background
echo "Starting API server..."
cd /Volumes/MacData/mydata/ai_server2/apiserver
python start_server.py &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Run test script
echo "Running test script..."
php test_spabot.php

# Kill server when done
echo "Killing server..."
kill $SERVER_PID

echo "Test completed."
