# VIL - Kurulum Kılavuzu

Bu kılavuz, VIL (Visual Intelligence Layer) platformunun kurulum adımlarını detaylı olarak açıklar.

## Ön Gereksinimler

### Sistem Gereksinimleri

- **İşletim Sistemi**: Linux (Ubuntu 20.04+), macOS (11+), Windows 10+
- **Python**: 3.9 veya üzeri
- **RAM**: Minimum 4GB (8GB önerilir)
- **Disk**: Minimum 10GB boş alan
- **Internet**: API erişimi için stabil bağlantı

### WordPress Gereksinimleri

- WordPress 5.0+
- REST API aktif
- Application Passwords özelliği aktif (WordPress 5.6+)
- Medya yükleme izinleri

### Opsiyonel Servisler

- **Google Cloud Vision API**: Gelişmiş görsel analizi için
- **Anthropic API**: Alternatif metadata üretimi için
- **Unsplash API**: Stok görsel arama için

## Adım Adım Kurulum

### 1. Repository Clone

```bash
git clone <repo-url>
cd vil
```

### 2. Python Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Bağımlılıkları Yükle

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Değişkenlerini Ayarla

```bash
cp .env.example .env
```

`.env` dosyasını düzenle:

```bash
# Google Cloud Vision API
GOOGLE_CLOUD_VISION_KEY=your-api-key-here

# Anthropic API (backup metadata)
ANTHROPIC_API_KEY=your-api-key-here

# WordPress - yoldaolmak.com
WP_USER=hamal
WP_PASSWORD=your-app-password-here

# WordPress - gezievreni.com (opsiyonel)
GEZIEVRENI_URL=https://gezievreni.com
GEZIEVRENI_USER=your-user
GEZIEVRENI_PASS=your-app-password

# WordPress - gezgindunyasi.com (opsiyonel)
GEZGINDUNYASI_URL=https://gezgindunyasi.com
GEZGINDUNYASI_USER=clawdbot
GEZGINDUNYASI_PASS=your-app-password

# VIL Dizin Ayarları
YO_VIL_DIR=/path/to/your/vil/images
YO_VISUAL_MEMORY_DB=/path/to/visual_memory.db
```

### 5. WordPress Application Password Oluştur

1. WordPress admin paneline giriş yap
2. **Kullanıcılar > Profil** sayfasına git
3. Aşağı kaydır, **Application Passwords** bölümünü bul
4. Yeni bir uygulama password oluştur (örn: "VIL System")
5. Oluşturulan password'u kopyala ve `.env` dosyasına ekle

### 6. Google Cloud Vision API Key Al (Opsiyonel)

1. [Google Cloud Console](https://console.cloud.google.com/)'a git
2. Yeni proje oluştur veya mevcut projeyi seç
3. **APIs & Services > Library**'ye git
4. "Cloud Vision API" ara ve aktif et
5. **APIs & Services > Credentials**'a git
6. **Create Credentials > API Key** oluştur
7. API key'i kopyala ve `.env` dosyasına ekle

### 7. İlk Çalıştırma Testi

```bash
# Sistem sağlık kontrolü
python scripts/yoos_vil_health.py

# VIL indeksleme (ilk kez çalıştırıyorsanız)
python scripts/index_vil.py
```

## Sorun Giderme

### Python Version Hatası

```bash
# Python version kontrol
python --version

# Eğer 3.9 altındaysa, güncelle
# Ubuntu:
sudo apt update
sudo apt install python3.9

# macOS (Homebrew):
brew install python@3.9
```

### Bağımlılık Çakışmaları

```bash
# Clean install
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

### WordPress Bağlantı Hatası

1. WordPress URL'in doğru olduğundan emin ol
2. Application Password'ün aktif olduğunu kontrol et
3. SSL certificate geçerli mi kontrol et
4. Firewall settings kontrol et

```bash
# Bağlantı testi
curl -u "username:app-password" https://yoursite.com/wp-json/wp/v2/posts
```

### Permission Hataları

```bash
# VIL dizini için write permission
chmod -R 755 /path/to/vil
chown -R $USER:$USER /path/to/vil
```

## Sonraki Adımlar

Kurulum tamamlandıktan sonra:

1. [Kullanım Kılavuzu](usage.md) - Temel kullanım senaryoları
2. [API Referansı](api-reference.md) - Detaylı API dokümantasyonu
3. [Mimari Detaylar](architecture.md) - Sistem mimarisini anlama

## Yardım

Sorun yaşarsanız:

- [GitHub Issues](https://github.com/your-repo/vil/issues) açın
- Dokümantasyonu kontrol edin
- Sistem loglarını inceleyin (`logs/` dizini)

---

*Son Güncelleme: Haziran 2024*
