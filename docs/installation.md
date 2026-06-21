# VIL Kurulum

Bugünkü kurulum iki parçalıdır: canonical uygulama repo'su ve varsa Mac Photos index runtime'ı.

## Canonical Repo

```bash
git clone <repo-url>
cd YOOS-VIL
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Temel local ayarlar:

```bash
cp .env.example .env
```

Minimum faydalı alanlar:

```bash
WP_USER=...
WP_PASSWORD=...
YO_VISUAL_MEMORY_DB=/Users/yoldaolmak/Downloads/YO_OS_VIL/data/visual_memory.db
```

`YO_VISUAL_MEMORY_DB` verilmezse repo kendi varsayılan boş DB yoluna bakar. Mac Photos ile çalışılacaksa bunu açık vermek gerekir.

## Mac Photos Index Runtime

Mac Photos index'i şu an ayrı çalışan runtime içinde tutuluyor:

```bash
cd /Users/yoldaolmak/Downloads/YO_OS_VIL
./.venv/bin/python -V
```

Buradaki virtualenv eski indexer ile uyumlu interpreter sağlar. Sistem `python3` 3.9 ise bu önemlidir.

Index kurulum akışı:

```bash
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 0
./.venv/bin/python extract_apple_photos_ml.py
```

Bu akış:

- Photos originals havuzunu indexler
- kalite kapısını uygular
- Apple ML blur/exposure/face verisini işler
- moment/location bilgisini `asset_index` içine yazar

## İlk Doğrulama

Canonical repo içinde:

```bash
python3 -m pytest -q
python3 -m src.vil.app.cli serve --help
python3 - <<'PY'
from src.main import search_semantic_assets
print(search_semantic_assets('Sinop', count=5))
PY
```

Beklenen durum:

- testler geçer
- CLI çalışır
- lokasyon sorgusu gerçek Mac Photos originals path'leri döndürür
