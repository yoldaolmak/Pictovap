# VIL Core - WordPress Otomatik Görsel Yerleştirme Motoru

Bu paket, VIL (Visual Intelligence Layer) sisteminin çekirdek modüllerini içerir.

## Modüller

### Orkestrasyon
- `yo_orchestrator.py`: Ana pipeline orkestrasyonu
- `yo_process.py`: Süreç yönetimi ve tracking

### Görsel İşleme
- `yo_image_processor.py`: Görsel optimizasyon ve transformasyon
- `yo_metadata_generator.py`: AI tabanlı meta veri üretimi

### Arama & Filtreleme
- `yo_semantic_search.py`: Vektör tabanlı semantik arama
- `yo_photo_filter.py`: Temel kalite filtreleme
- `yo_advanced_filter.py`: Gelişmiş filtre kuralları
- `yo_adaptive_filter.py`: Dinamik adaptif filtreleme
- `yo_yoldaolmak_filter.py`: Domain-spesifik filtreler

### AI & Tagging
- `yo_clip_tagger.py`: CLIP model entegrasyonu
- `yo_semantic_tagger.py`: Semantik etiketleme
- `yo_cloud_vision.py`: Google Cloud Vision entegrasyonu
- `yo_face_detector.py`: Yüz algılama (opsiyonel)
- `yo_tag_taxonomy.py`: Etiket taksonomisi yönetimi

### WordPress Entegrasyonu
- `yo_wp_uploader.py`: Media uploader
- `yo_wp_draft_image_cycle.py`: Draft post image cycling
- `yo_gutenberg_blocks.py`: Gutenberg block desteği

### Yardımcı Araçlar
- `media_publish.py`: Medya yayınlama utilities
- `media_quality.py`: Kalite kontrol araçları
- `yo_unsplash.py`: Unsplash API entegrasyonu
- `yo_iphoto.py`: Apple Photos entegrasyonu
- `yo_quality_comparison.py`: Kalite karşılaştırma
- `yo_phase1_quick_tagger.py`: Hızlı etiketleme
- `yo_full_tagger_pipeline.py`: Tam tagging pipeline
- `yo_vision_daily_scan.py`: Günlük Vision taraması

### Konfigürasyon
- `settings.py`: Ana ayarlar ve environment yönetimi
