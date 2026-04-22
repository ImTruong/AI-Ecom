#!/bin/bash
echo ">>> Knowledge Service Starting..."
echo ">>> Waiting for Neo4j (15s)..."
sleep 15
echo ">>> Starting Data Import from CSV..."
python importer.py
echo ">>> Data Import Finished. Starting API Service..."
python main.py
