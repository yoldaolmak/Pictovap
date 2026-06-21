# VIL Kullanım

Bu repo için çalışan yüzey artık `vil` CLI ve minimal HTTP app'tir. Eski `yo_orchestrator` örnekleri bugünkü ana kullanım yüzeyi değildir.

## Temel Akış

İçeriğe görsel ekleme işi pratikte dört adımdır:

```bash
vil review --site yoldaolmak --post 265713
vil plan --site yoldaolmak --post 265713 --count 4 --people-first
vil process --site yoldaolmak --post 265713 --count 4 --people-first
vil attach --site yoldaolmak --post 265713 --count 4 --people-first
```

`review` post bağlamını döner. `plan` adayları gösterir. `process` seçilen dosyaları işler ama publish etmez. `attach` publish dahil tam akışı çalıştırır.

## Native Akış

Yeni ürün yüzeyi `native` engine ile test edilebilir:

```bash
vil attach --site yoldaolmak --post 265713 --count 4 --people-first --engine native
```

## HTTP Akış

```bash
vil serve --host 127.0.0.1 --port 8040
```

Sonra:

```bash
curl -s http://127.0.0.1:8040/health

curl -s -X POST http://127.0.0.1:8040/plan \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":265713,"count":4,"people_first":true}'
```

Uzun süren attach işlemi için:

```bash
curl -s -X POST http://127.0.0.1:8040/jobs/attach \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":265713,"count":4,"people_first":true}'
```

Bu çağrı `job_id` döner. Sonra `GET /jobs/{job_id}` ile durum sorgulanır.

## Mac Photos Kullanımı

Mac Photos görselleri önce ayrı visual memory runtime içinde indexlenir, sonra canonical repo bu DB'yi kullanır.

Index ve enrich:

```bash
cd /Users/yoldaolmak/Downloads/YO_OS_VIL
./.venv/bin/python index_memory_daily.py --mode photos --daily-limit 0
./.venv/bin/python extract_apple_photos_ml.py
```

Canonical repo için local `.env`:

```bash
YO_VISUAL_MEMORY_DB=/Users/yoldaolmak/Downloads/YO_OS_VIL/data/visual_memory.db
```

Bu kurulduktan sonra semantic arama Mac Photos asset'lerini lokasyon metadata'sı üzerinden seçebilir.

Örnek doğrulama:

```bash
python3 - <<'PY'
from src.main import search_semantic_assets
print(search_semantic_assets('Sinop', count=5))
PY
```

## Pratik Notlar

Mac Photos hattı çalışsa bile WordPress credential yoksa `attach` publish aşamasında durur. Bu durumda `review`, `plan` ve `process` yine kullanılabilir.

Semantic seçim artık sadece dosya yoluna değil, indexteki `location`, `city`, `country`, `title`, `description`, `summary`, `activity` ve `scene` alanlarına da bakar.
