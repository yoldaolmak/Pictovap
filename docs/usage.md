# VIL - Kullanım Kılavuzu

Bu kılavuz, VIL (Visual Intelligence Layer) platformunun günlük kullanım senaryolarını ve komutlarını açıklar.

## Temel Kavramlar

### POST ID
WordPress'te her yazının benzersiz kimlik numarası. Örnek: `https://yoldaolmak.com/roma-gezisi/` yazısının ID'si `12345` olabilir.

### H Başlıkları
İçerikteki başlık seviyeleri (H1, H2, H3, ...). VIL, her başlık bölümüne uygun görseller yerleştirir.

### VIL Dizin
Görsellerin bulunduğu kaynak dizin. `.env` dosyasında `YO_VIL_DIR` ile tanımlanır.

### Visual Memory
Görsellerin metadata ve embedding'lerinin saklandığı veritabanı.

## Kullanım Senaryoları

### Senaryo 1: Tek Bir Yazıya Görsel Ekleme

En temel kullanım. Belirli bir POST ID'ye sahip yazıya otomatik görsel ekler.

```bash
python -m src.core.yo_orchestrator --post-id 12345
```

**Ne yapar:**
1. Yazıyı WordPress'ten çeker
2. H başlıklarını tespit eder
3. Her başlık için 2 adet uygun görsel bulur
4. Görselleri optimize eder
5. WordPress'e yükler
6. İçeriğe yerleştirir

### Senaryo 2: Birden Fazla Yazıya Toplu İşlem

Birden fazla POST ID'yi virgülle ayırarak toplu işlem yapabilirsin.

```bash
python -m src.core.yo_orchestrator --post-ids 12345,12346,12347,12348
```

### Senaryo 3: Kategori Bazlı İşlem

Belirli bir kategorideki son X yazıya görsel ekle.

```bash
python -m src.core.yo_orchestrator --category "seyahat" --limit 50
```

### Senaryo 4: Test Modu (Dry Run)

Sistemi test etmek istiyorsan, hiçbir değişiklik yapmadan simülasyon yapabilirsin.

```bash
python -m src.core.yo_orchestrator --post-id 12345 --dry-run --verbose
```

### Senaryo 5: Özelleştirilmiş Parametreler

Her başlık için farklı sayıda görsel, kalite threshold'u vb. ayarlayabilirsin.

```bash
python -m src.core.yo_orchestrator \
  --post-id 456 \
  --images-per-heading 3 \
  --min-image-width 1200 \
  --quality-threshold 0.8 \
  --verbose
```

## Komut Satırı Parametreleri

| Parametre | Kısa | Açıklama | Varsayılan |
|-----------|------|----------|------------|
| `--post-id` | `-p` | Tek post ID | - |
| `--post-ids` | `-i` | Virgülle ayrılmış ID listesi | - |
| `--category` | `-c` | WordPress kategori slug | - |
| `--limit` | `-l` | İşlenecek maksimum post sayısı | 10 |
| `--images-per-heading` | `-n` | Başlık başına görsel sayısı | 2 |
| `--min-image-width` | `-w` | Minimum görsel genişliği (px) | 800 |
| `--quality-threshold` | `-q` | Kalite skoru eşiği (0-1) | 0.7 |
| `--heading-levels` | `-H` | İşlenecek başlık seviyeleri | H1,H2,H3 |
| `--dry-run` | `-d` | Değişiklik yapmadan simüle et | False |
| `--verbose` | `-v` | Detaylı log çıktısı | False |
| `--force` | `-f` | Mevcut görselleri overwrite et | False |
| `--site` | `-s` | Hedef WordPress sitesi | yoldaolmak |

## Gelişmiş Kullanım

### Farklı WordPress Siteleri

VIL, birden fazla WordPress sitesini destekler.

```bash
# Gezievreni.com için
python -m src.core.yo_orchestrator --post-id 789 --site gezievreni

# GezginDunyasi.com için
python -m src.core.yo_orchestrator --post-id 101 --site gezgindunyasi
```

### Belirli Başlık Seviyeleri

Sadece H2 ve H3 başlıklarına görsel ekle:

```bash
python -m src.core.yo_orchestrator \
  --post-id 12345 \
  --heading-levels "H2,H3" \
  --skip-h1
```

### Batch Processing (Toplu İşlem)

Yüzlerce yazıyı sırayla işle:

```bash
# Son 100 seyahat yazısı
python -m src.core.yo_orchestrator \
  --category "seyahat" \
  --limit 100 \
  --images-per-heading 1 \
  --verbose

# Logları takip et
tail -f logs/orchestrator.log
```

## Operasyonel Scriptler

### Sistem Sağlık Kontrolü

```bash
python scripts/yoos_vil_health.py
```

**Kontrol eder:**
- WordPress bağlantısı
- API key'lerin geçerliliği
- VIL dizinin erişilebilirliği
- Visual Memory DB durumu

### VIL İndeksleme

```bash
# Tüm VIL görsellerini indeksle
python scripts/index_vil.py

# Günlük incremental indeksleme
python scripts/index_memory_daily.py
```

### Görsel Onarım

```bash
# Görsel yerleşim hatalarını düzelt
python scripts/repair_image_placement.py

# Türkçe metadata onarımı
python scripts/repair_turkish_media_meta.py
```

### Bütçe Takibi

```bash
# Vision API kullanım takibi
python scripts/vision_budget.py
```

## Çıktı ve Loglar

### Console Çıktısı

Normal mod:
```
[INFO] Processing post 12345: "Roma Gezisi"
[INFO] Found 8 headings
[INFO] Selected 16 images
[INFO] Uploaded 16 images to WordPress
[SUCCESS] Completed post 12345 in 45.2s
```

Verbose mod:
```
[DEBUG] Fetching post 12345 from WordPress...
[DEBUG] Parsing headings...
[DEBUG] H2: "Roma'nın Tarihi" → searching images...
[DEBUG] Found 23 candidates, filtering...
[DEBUG] Selected: IMG_1234.jpg (score: 0.89)
[INFO] Uploading IMG_1234.jpg...
[DEBUG] Upload successful, media_id: 5678
...
```

### Log Dosyaları

Loglar `logs/` dizininde tutulur:

- `orchestrator.log`: Ana pipeline logları
- `uploader.log`: Upload işlemleri
- `vision.log`: Google Vision API çağrıları
- `error.log`: Hatalar ve exception'lar

## Sık Karşılaşılan Durumlar

### "No Images Found" Uyarısı

Eğer bir başlık için uygun görsel bulunamazsa:

1. Quality threshold'u düşür: `--quality-threshold 0.5`
2. Daha geniş VIL dizini kullan
3. Manual review için flag'le

```bash
python -m src.core.yo_orchestrator \
  --post-id 12345 \
  --quality-threshold 0.5 \
  --flag-for-review
```

### Upload Timeout

Büyük görsellerde timeout oluşursa:

1. Maximum image width'i azalt: `--max-image-width 1200`
2. Internet bağlantısını kontrol et
3. Retry logic otomatik devreye girer

### API Rate Limit

API limitlerine takılırsan:

```bash
# Daha yavaş çalıştır
python -m src.core.yo_orchestrator \
  --post-ids 1,2,3,4,5 \
  --delay-between-requests 2
```

## Best Practices

### 1. Dry-Run ile Başla

Yeni bir batch işlemine başlamadan önce mutlaka dry-run yap:

```bash
python -m src.core.yo_orchestrator --category "seyahat" --limit 5 --dry-run
```

### 2. Küçük Batch'lerle Çalış

100'den fazla post'u tek seferde işleme:

```bash
# İyi
python -m src.core.yo_orchestrator --category "seyahat" --limit 50

# Kötü
python -m src.core.yo_orchestrator --category "seyahat" --limit 500
```

### 3. Verbose Modu Kullan

İlk birkaç işlemi verbose modda çalıştır ki sistemi anlayabilirsin:

```bash
python -m src.core.yo_orchestrator --post-id 12345 --verbose
```

### 4. Logları Düzenli Kontrol Et

```bash
# Hataları takip et
tail -f logs/error.log

# Bugünkü işlemleri gör
grep "$(date +%Y-%m-%d)" logs/orchestrator.log
```

### 5. Backup Al

Önemli batch işlemlerinden önce WordPress backup'ı al.

## Sonraki Adımlar

- [API Referansı](api-reference.md) - Programatik kullanım
- [Mimari Detaylar](architecture.md) - Sistem nasıl çalışır
- [Güvenlik](security.md) - Güvenlik best practices

---

*Son Güncelleme: Haziran 2024*
