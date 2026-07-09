#!/bin/bash
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting Pictova Auto Scan Loop..."
echo "As Mac Photos downloads originals from iCloud, this script will detect and scan them."
while true; do
    echo "--------------------------------------------------------"
    echo "🔍 [$(date)] 1. Step: Indexing newly downloaded photos..."
    python3.11 scripts/index_turkey_photos.py > /dev/null 2>&1
    
    echo "🤖 [$(date)] 2. Step: Scanning downloaded photos with Gemini..."
    python3.11 scripts/fast_scan.py --workers 1
    
    echo "⏳ [$(date)] 3. Step: Waiting 5 minutes for new downloads..."
    sleep 300
done
