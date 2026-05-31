Kisa yanit, gereksiz kod verme, aciklama yapma.

Calisma klasoru varsayilan: /Users/KemalKaya/YO_OS_VIL

VIL gorsel hazirlama kurali (zorunlu):
- Kaynak klasor kullanici net verdiyse sadece o klasor taranir
- H2/H3 basliklari sadece esleme icin kullanilir; dosya adina baslik metni cakilmaz
- Rename semantik olmalı (resim ne anlatiyorsa), 5-6 kelimeyi gecmez
- `genel`, anlamsiz numerik suffix ve baslik kopyasi isimler yasak
- Google Vision sadece free kota ile (YO_GCV_FREE_ONLY=1), gerekiyorsa semantic dogrulama icin kullan
- Cikis once `~/Downloads/VIL` altina hazirlanir (crop+filter+metadata)

Depositphotos otomatik kural:
- Kullanici "indir", "foto getir", "Cordoba panoramik fotoğraf getir", "DP'den getir" benzeri istek yazdiginda soru sorma
- Dogrudan su komutu calistir:
  cd /Users/KemalKaya/photo_ai && python3 run_deposit.py "<kullanici sorgusu>"
- Varsayilan kayit yolu ~/Downloads, format webp, crop standart
- Hata varsa sadece net hata + tekrar denenecek komutu yaz
