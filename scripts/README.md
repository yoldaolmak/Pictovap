# VIL Scripts - Bakım ve Operasyonel Scriptler

Bu klasör, VIL sistemi için bakım, indeksleme ve operasyonel scriptleri içerir.

## Scriptler

### İndeksleme
- `index_vil.py`: VIL görsellerini indeksleme
- `index_memory_daily.py`: Günlük visual memory indeksleme

### Veri Çıkarma
- `extract_apple_photos_ml.py`: Apple Photos ML metadata çıkarma

### Onarım
- `repair_image_placement.py`: Görsel yerleşim onarımı
- `repair_turkish_media_meta.py`: Türkçe media meta onarımı

### İndirme & Yükleme
- `download_licensed_deposit_assets.py`: Lisanslı deposit varlıkları indirme
- `run_deposit.py`: Deposit işlem çalıştırma

### Sağlık & İzleme
- `yoos_vil_health.py`: Sistem sağlık kontrolü
- `vision_budget.py`: Vision API bütçe takibi

## Kullanım

```bash
# VIL indeksleme
python scripts/index_vil.py

# Günlük memory indeksleme
python scripts/index_memory_daily.py

# Sistem sağlık kontrolü
python scripts/yoos_vil_health.py
```
