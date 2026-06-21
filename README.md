# YOOS-VIL

YOOS-VIL, WordPress yazılarına içerikle uyumlu görseller seçmek, işlemek ve yerleştirmek için kullanılan görsel pipeline repo'sudur.

Bu repo şu an iki yüzey sunuyor:

- `vil` CLI
- minimal HTTP app surface

## Çalışan Yüzey

### CLI

```bash
vil health
vil review --site yoldaolmak --post 264459
vil plan --site yoldaolmak --post 264459 --count 4 --people-first
vil process --site yoldaolmak --post 264459 --count 4 --people-first
vil attach --site yoldaolmak --post 264459 --count 4 --people-first
vil attach --site yoldaolmak --post 264459 --count 4 --people-first --engine native
```

### HTTP

```bash
vil serve --host 127.0.0.1 --port 8040
```

Endpoints:

- `GET /`
- `GET /health`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `POST /review`
- `POST /plan`
- `POST /process`
- `POST /attach`
- `POST /jobs/attach`

Örnek:

```bash
curl -s http://127.0.0.1:8040/health

curl -s -X POST http://127.0.0.1:8040/plan \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":264459,"count":4,"people_first":true}'

curl -s -X POST http://127.0.0.1:8040/jobs/attach \
  -H 'Content-Type: application/json' \
  -d '{"site":"yoldaolmak","post_id":264459,"count":4,"people_first":true}'
```

`POST /jobs/attach` senkron cevap yerine job kaydı döner. Sonra `GET /jobs/{job_id}` ile durum sorgulanır.

## Native ve Legacy

- `legacy`: mevcut orkestratörü sarar, bugün en tam davranış burada
- `native`: yeni `src/vil/*` yüzeyini kullanır; seçim, işleme, kalite kapısı ve publish kontratı ayrıştırılmıştır

Bugünkü durum:

- native `plan` hazır
- native `process` hazır
- native `attach` çalışır
- native metadata, API anahtarı varsa vision analizi dener
- anahtar yoksa deterministic fallback metadata kullanır

## Repo Yapısı

```text
src/
  vil/
    app/
    engine/
    profiles/
    providers/
  core/
  services/
  utils/
ops/
tests/
docs/
```

## Doğrulama

Son doğrulanan komutlar:

```bash
python3 -m pytest -q
python3 -m src.vil.app.cli attach --help
python3 -m src.vil.app.cli plan --help
python3 -m src.vil.app.cli process --help
python3 -m src.vil.app.cli serve --help
```

Son test durumu:

- `18 passed, 1 warning`

## Eksik Olanlar

- native hattın legacy kadar zengin semantic metadata üretmesi
- gerçek job state / queue / progress yüzeyi
- HTTP surface için auth
- persisted job store
- structured logging
- retry politikası
- legacy çekirdeğin kademeli olarak `src/vil/*` altına taşınması
