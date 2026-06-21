# VIL Architecture

## Çalışan Yapı

Repo bugün iki katmanlı çalışıyor: canonical uygulama yüzeyi `src/vil/*` altında, mevcut seçim ve publish çekirdeğinin bir kısmı ise hâlâ legacy modüller üzerinden sarılıyor.

## Uygulama Yüzeyi

`src/vil/app/` altında üç ana giriş var:

- `cli.py`: `vil` komutları
- `api.py`: Python-callable ince yüzey
- `server.py`: minimal HTTP surface

Bunların üstünde `state.py` ile job kaydı tutulur.

## Engine Katmanı

`src/vil/engine/` seçimi, işleme, metadata, kalite kapısı ve publish akışını parçalara ayırır.

Ana modüller:

- `attach.py`
- `selector.py`
- `processor.py`
- `metadata.py`
- `quality.py`
- `publisher.py`

## Legacy Bağımlılık

Bugünkü canonical seçim hattı hâlâ bazı noktalarda `src/main.py` ve `src/core/*` içindeki mevcut davranışı kullanır. Özellikle semantic seçim ve bazı publish davranışları tamamen native hale gelmiş değildir.

## Visual Memory Akışı

Mac Photos tarafı doğrudan canonical repo içinde indexlenmiyor. Çalışan index runtime şu anda `/Users/yoldaolmak/Downloads/YO_OS_VIL` altında.

Bu runtime:

- Photos originals dosyalarını keşfeder
- kalite ve seçim skoru üretir
- `asset_index` tablosuna yazar
- Apple Photos ML verisini aynı tabloya enrich eder

Canonical repo ise bu DB'yi `YO_VISUAL_MEMORY_DB` ile kullanır.

## Semantic Seçim

Semantic seçim eskiden ağırlıkla `source_path` eşleşmesine dayanıyordu. Güncel halde seçim şu index alanlarında da eşleşme arar:

- `filename`
- `title`
- `description`
- `summary`
- `location`
- `city`
- `country`
- `activity`
- `scene`

Bu değişiklik Mac Photos asset'lerinin UUID path yapısından dolayı zorunluydu; aksi halde lokasyon bazlı post eşleşmesi çalışmıyordu.

## HTTP Yüzeyi

Bugünkü HTTP surface minimaldir:

- `GET /health`
- `POST /review`
- `POST /plan`
- `POST /process`
- `POST /attach`
- `POST /jobs/attach`
- `GET /jobs`
- `GET /jobs/{job_id}`

Bu yüzey şu an auth ve persisted job store olmadan çalışır.
