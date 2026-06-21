# VIL Tests - Test Suite

Bu klasör, VIL sistemi için testleri içerir.

## Test Yapısı

```
tests/
├── unit/           # Unit testler
│   ├── test_image_processor.py
│   ├── test_metadata_generator.py
│   ├── test_semantic_search.py
│   └── ...
├── integration/    # Integration testler
│   ├── test_wp_uploader.py
│   ├── test_orchestrator.py
│   └── ...
└── __init__.py
```

## Test Çalıştırma

```bash
# Tüm testleri çalıştır
pytest tests/

# Sadece unit testler
pytest tests/unit/

# Sadece integration testler
pytest tests/integration/

# Coverage raporu ile
pytest --cov=src --cov-report=html
```

## Test Coverage Hedefi

- Q2 2024: %40 (mevcut)
- Q3 2024: %60
- Q4 2024: %80+

## Yeni Test Ekleme

1. Test edilecek modülü belirle
2. `tests/unit/` veya `tests/integration/` altında uygun dosyayı oluştur
3. pytest konvansiyonlarına uygun test fonksiyonları yaz
4. Mock external APIs (requests, Google Vision, vb.)
5. Testleri çalıştır ve coverage kontrol et

```python
# Örnek unit test
def test_image_processor_resize():
    processor = YOImageProcessor()
    result = processor.resize_image("test.jpg", 800, 600)
    assert result.width == 800
    assert result.height <= 600
```
