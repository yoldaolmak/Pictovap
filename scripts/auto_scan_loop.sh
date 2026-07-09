#!/bin/bash
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Pictova Otomatik Tarama Döngüsü Başlatılıyor..."
echo "Mac Fotoğraflar uygulaması iCloud'dan orijinalleri indirdikçe, bu betik onları tespit edip tarayacaktır."
while true; do
    echo "--------------------------------------------------------"
    echo "🔍 [$(date)] 1. Adım: Yeni inen fotoğraflar indeksleniyor..."
    python3.11 scripts/index_turkey_photos.py > /dev/null 2>&1
    
    echo "🤖 [$(date)] 2. Adım: İnen fotoğraflar Gemini ile taranıyor..."
    python3.11 scripts/fast_scan.py --workers 1
    
    echo "⏳ [$(date)] 3. Adım: Yeni indirmeler için 5 dakika bekleniyor..."
    sleep 300
done
