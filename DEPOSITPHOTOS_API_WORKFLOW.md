# Depositphotos API Workflow Standard

Bu dosya, `photo_ai` icinde Depositphotos API ile yapilan arama, secim, preview export, lisansli export ve metadata embed akislarini standartlastirmak icin tutulur.

Amac:
- terminal kopsa bile ayni is akisini tekrar kurabilmek
- hangi adimda kalindigini tek dosyadan anlayabilmek
- log, rollback ve output isimlendirmesini sabit tutmak
- gecici sohbet baglamina degil, repo icindeki kalici kayitlara dayanmak

## 1. Canonical Sources

Depositphotos ile ilgili karar verirken once su kaynaklar okunur:

1. `depositphotos_credentials.json`
2. `ops_logs/` altindaki en yeni `depositphotos_*` loglari
3. `visual_memory/stock.py`
4. `visual_memory/seo.py`
5. bu dosya

Konusma hafizasi veya gecici terminal ciktisi, bu dosyalardaki kayitlarla celisirse repo icindeki kayit esas alinur.

## 2. Required Inputs

Bir Depositphotos gorevi baslatmadan once su bilgiler net olmalidir:

- konu: ornek `Piazza Barberini`
- orientation: `landscape`, `portrait`, `square`
- kullanim tipi:
  - `preview_export`
  - `licensed_export`
- hedef output klasoru
- hedef dosya adi
- metadata hedefi:
  - sadece indir
  - indir ve SEO metadata gom

## 3. Standard Query Format

Arama sorgusu su kalipla yazilir:

`<place> <city> orientation <orientation>`

Ornekler:

- `piazza barberini rome orientation landscape`
- `palatine hill rome orientation vertical`
- `piazza navona rome orientation square`

Gerekirse ikinci sorgu varyanti:

`<place> <city> <subject keywords> orientation <orientation>`

## 4. Standard Output Paths

Tum ciktilar acik bir hedefe yazilmalidir:

- tekli gecici cikti: `~/Downloads/`
- yayin seti: `~/Downloads/roma-gezi-rehberi-yayina-hazir/`
- secili harici set: `~/Downloads/roma_gezi_rehberi_external_selected/`

> `MÜ` kisaltmasi bu dosyada `Masaüstü` anlamina gelir ve ayni zamanda geliştirici masaüstü konumunu gösteren `Downloads` klasörünü ifade eder. Tum Depositphotos ciktilari yukaridaki `~/Downloads/` agacinin icinde saklanir ve masaüstunden gelen islemler icin ayni dosya yolu kullanilir.

> `MÜ` kisaltmasi bu dosyada `Masaüstü` anlamina gelir ve ayni zamanda geliştirici masaüstü konumunu gösteren `Downloads` klasörünü ifade eder. Tum Depositphotos ciktilari yukaridaki `~/Downloads/` agacinin icinde saklanir ve masaüstunden gelen islemler icin ayni dosya yolu kullanilir.

Dosya isimleri:

- kucuk harf
- kelimeler `-` ile ayrilir
- yer ve konu once gelir
- orientation gerekiyorsa sona eklenir

Ornekler:

- `piazza-barberini-triton-fountain-landscape.webp`
- `piazza-barberini-square-view.webp`

## 5. Mandatory Logging

Her Depositphotos operasyonu icin `ops_logs/` altina bir log yazilmalidir.

Dosya adi:

`YYYY-MM-DD_<operation_name>.log`

Eslesik rollback:

`YYYY-MM-DD_<operation_name>.rollback.sh`

Log icinde asgari su alanlar bulunur:

```text
timestamp: YYYY-MM-DD HH:MM:SS
operation: <operation_name>
api_source: https://api.depositphotos.com/
search_query: <query>
orientation: <landscape|portrait|square>
mode: <preview_export|licensed_export>
selected_asset_id: <asset id or empty>
selected_item_url: <landing url or empty>
selected_preview_url: <preview url or empty>
output: <absolute output path>
license_id: <license id or empty>
metadata_embed: <pending|done|skipped|failed>
status: <started|completed|failed>
notes:
- <free text>
```

Birden fazla cikti varsa `outputs:` bolumu kullanilir.

## 6. Mandatory Rollback

Her export isinde rollback scripti yazilmalidir.

Minimum rollback:

```bash
#!/bin/bash
rm -f "<absolute output path>"
```

Birden fazla dosya varsa hepsi tek rollback dosyasina yazilmalidir.

Rollback scripti, log ile ayni operasyon adini tasimalidir.

## 7. Resume Protocol

Terminal kesilirse veya oturum kapanirsa su sirayla devam edilir:

1. `ops_logs/` altinda ilgili operasyonun en yeni logunu bul
2. `status:` alanina bak
3. `selected_asset_id`, `license_id`, `output`, `metadata_embed` alanlarini kontrol et
4. output dosyasi gercekten var mi dogrula
5. eksik kalan ilk adimdan devam et

Kurallar:

- `status: completed` ise ayni isi yeniden baslatma
- output yoksa ama log var ise is yarim kalmistir
- output var ama `metadata_embed: pending` ise sadece metadata adimi calistirilir
- `license_id` bos ise lisansli export tamamlanmis sayilmaz

## 8. State Model

Her operasyon su durumlardan birinde olmalidir:

- `started`
- `api_search_done`
- `asset_selected`
- `preview_export_done`
- `licensed_export_done`
- `metadata_embedded`
- `completed`
- `failed`

Yeni log yazarken son durum acikca belirtilmelidir.

## 9. Metadata Standard

Export sonrasi metadata gomulecekse [visual_memory/seo.py](/Users/KemalKaya/photo_ai/visual_memory/seo.py) kurallari esas alinir.

Beklenen alanlar:

- `title`
- `caption`
- `description`
- `keywords`
- `credit`

Notlar:

- `description` her zaman `kaynak: 📷 Depositphotos` ile bitmelidir
- `title` ve `caption` kisa olmalidir
- `alt` degeri uretilse bile dosyaya dogrudan yazilmiyorsa bu logda not edilmelidir

## 10. Verification Checklist

Bir operasyon `completed` olmadan once su kontroller yapilmalidir:

1. API aramasi yapildi
2. secilen `asset_id` loglandi
3. output dosyasi olustu
4. rollback scripti olustu
5. metadata embed sonucu loglandi
6. preview ve lisansli export birbirine karistirilmadi

## 11. Failure Handling

Asagidaki durumlarda operasyon `failed` yazilmalidir:

- API endpoint `404`
- auth hatasi
- lisans akisi tamamlanamadi
- output dosyasi olusmadi
- metadata embed komutu hata verdi

Hata logu su formatta olmalidir:

```text
status: failed
failure_stage: <api_search|asset_select|preview_export|licensed_export|metadata_embed>
failure_reason: <short explanation>
next_action: <what to do next>
```

## 12. Current Repo Gaps

Bu repo icinde su an bilinen bosluklar vardir:

- `visual_memory/stock.py` icinde helper method yerlesimi bozuk, client normalize akisi kirik
- mevcut `search_url` yeniden dogrulanmali, bugun ayni endpoint ile `404` goruldu
- onceki calisan akis loglarda var ama komut/scripte kalici olarak alinmamis

Bu dosya, bu bosluklar giderilene kadar operasyonel referans olarak kullanilacaktir.

## 13. Next Implementation Rule

Depositphotos API ile ilgili bir sonraki kod degisikligi yapildiginda:

1. client bug fix
2. endpoint/config dogrulama
3. standart log yazimi
4. rollback yazimi
5. resume-safe state dosyasi veya log status guncellemesi

Bu bes adim ayni patch icinde ele alinmalidir.
