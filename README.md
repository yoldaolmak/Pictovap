# VIL - Visual Intelligence Layer

**Premium WordPress Otomatik Görsel Yerleştirme Platformu**

VIL, WordPress içerik yönetim sisteminde yayınlanan yazılardaki başlık (H1, H2, H3...) yapılarını analiz ederek, her bölüm için en uygun görselleri otomatik olarak bulan, işleyen ve yerleştiren yapay zeka destekli bir platformdur.

## 🎯 Değer Önermesi

- **Zaman Tasarrufu**: Manuel görsel arama ve yükleme sürecini %90 azaltır
- **İçerik Kalitesi**: Her başlık için semantik olarak en alakalı görselleri seçer
- **SEO Optimizasyonu**: Görsellere otomatik alt text, başlık ve açıklama meta verileri ekler
- **Ölçeklenebilirlik**: Tek bir komutla yüzlerce yazıyı işleyebilir
- **Multi-Site Desteği**: Birden fazla WordPress sitesini yönetebilir

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.9+
- WordPress REST API erişimi
- (Opsiyonel) Google Cloud Vision API
- (Opsiyonel) Unsplash API
- PostgreSQL/MySQL (görsel metadata indexing için)

### Kurulum

```bash
# 1. Repository clone
git clone <repo-url>
cd vil

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Bağımlılıklar
pip install -r requirements.txt

# 4. Environment ayarları
cp .env.example .env
# .env dosyasını düzenle

# 5. İlk çalıştırma
python scripts/yoos_vil_health.py
```

### Temel Kullanım

```bash
# Tek Post ID için görsel ekleme
python -m src.core.yo_orchestrator --post-id 12345

# Birden fazla Post ID
python -m src.core.yo_orchestrator --post-ids 12345,12346,12347

# Belirli bir kategorideki tüm postlar
python -m src.core.yo_orchestrator --category "seyahat" --limit 50

# Dry-run (test modu)
python -m src.core.yo_orchestrator --post-id 12345 --dry-run
```

## 📚 Dokümantasyon

- [Kurulum Kılavuzu](docs/installation.md)
- [Kullanım Kılavuzu](docs/usage.md)
- [API Referansı](docs/api-reference.md)
- [Mimari Detaylar](docs/architecture.md)
- [Güvenlik Best Practices](docs/security.md)

## 🏗️ Proje Yapısı

```
vil/
├── src/
│   ├── core/           # Ana pipeline bileşenleri
│   │   ├── yo_orchestrator.py
│   │   ├── yo_image_processor.py
│   │   ├── yo_metadata_generator.py
│   │   └── ...
│   ├── ai/             # AI/ML modülleri (gelecek)
│   ├── integrations/   # Third-party entegrasyonlar (gelecek)
│   └── utils/          # Yardımcı araçlar
├── scripts/            # Operasyonel scriptler
├── tests/              # Test suite
│   ├── unit/
│   └── integration/
├── docs/               # Dokümantasyon
├── .env.example        # Environment şablonu
├── requirements.txt    # Python bağımlılıkları
└── README.md           # Bu dosya
```

## 🔧 Özellikler

### Core Pipeline

1. **İçerik Analizi**
   - WordPress'ten POST ID al
   - H başlıklarını parse et
   - Her bölüm için bağlam çıkar

2. **Görsel Arama & Seçim**
   - Vektör tabanlı semantik arama
   - Kalite filtreleme
   - Gelişmiş kriterler
   - Dinamik adaptasyon

3. **Görsel İşleme**
   - Boyutlandırma, optimizasyon
   - AI ile meta veri üretimi
   - CLIP modeli ile etiketleme
   - Google Vision analizi

4. **WordPress Entegrasyonu**
   - Medya kütüphanesine yükleme
   - Taslaklara yerleştirme
   - Block editörü uyumlu

5. **Orkestrasyon**
   - Tüm pipeline'ı yönetir
   - Süreç takibi ve loglama

## 🛣️ Roadmap

### Q2 2024 (Mevcut Faz)
- ✅ Core pipeline implementation
- ✅ Semantic search integration
- ✅ Basic metadata generation
- ⏳ Test coverage iyileştirme
- ⏳ Documentation completion

### Q3 2024
- [ ] Advanced AI features (multi-modal understanding)
- [ ] Real-time progress dashboard
- [ ] Batch processing optimization (parallel execution)
- [ ] Custom taxonomy support

### Q4 2024
- [ ] Multi-site WordPress support
- [ ] Plugin olarak packaging (WordPress plugin repo)
- [ ] Web UI for non-technical users
- [ ] Analytics & reporting module

### 2025+
- [ ] Video content support
- [ ] Multi-language content handling
- [ ] ML model training on custom dataset
- [ ] CDN integration for faster delivery

## 🤝 Katkıda Bulunma

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Style

- PEP 8 compliant
- Type hints kullanımı zorunlu
- Docstrings (Google style) her public method için
- Maximum line length: 100 characters

### Commit Messages

```
feat: add semantic search caching
fix: resolve image upload timeout issue
docs: update README with usage examples
refactor: extract metadata generation to separate module
test: add unit tests for YoImageProcessor
```

## 🔐 Güvenlik

- Tüm API credentials `.env` dosyasında tutulur
- SQL injection prevention (prepared statements)
- Rate limiting ve throttling
- Input validation ve sanitization
- Sensitive information masking in logs

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakınız.

## 👥 İletişim

**Proje Lead**: Kemal  
**Repository**: [GitHub](your-repo-url)  
**Issue Tracker**: [GitHub Issues](your-issues-url)  

---

*Son Güncelleme: Haziran 2024*  
*Versiyon: 2.0.0*
