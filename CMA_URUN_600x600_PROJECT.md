# CMA Urun 800x800 Beyaz Arka Plan Standardizasyonu

## Kaynak
- Girdi klasoru: `/root/tmp/CMA Urun`
- Hedef: Bu klasordeki urun gorsellerini tek tek isleyip tutarli e-ticaret urun gorsellerine donusturmek

## Cikti Kurallari
- Her gorsel `800x800` piksel olacak
- Tuval formati kare olacak
- Arka plan duz beyaz olacak: `RGB(255,255,255)`
- Gradyan, desen, doku olmayacak
- Urun kadrajda tam ortalanacak
- Dort kenarda esit bosluk olacak
- Golge, cerceve, kenarlik, kontur olmayacak
- Urun uzerindeki yazi, logo, barkod, fiyat etiketi korunacak
- Tum gorseller ayni kamera acisi ve isik duzeninde cekilmis gibi tutarli gorunecek
- Her gorsel ayri dosya olarak kaydedilecek

## Isleme Notlari
- Perspektif veya urun geometrisi bozmayacak
- Arka plan temizligi urun sinirlarini bozmayacak
- Ambalaj rengi ve baski detaylari korunacak
- Farkli oranli kaynaklarda urun maksimum gorunur boyutta tutulurken esit margin korunacak

## Beklenen Teslim
- Islenmis gorseller icin ayri bir cikti klasoru
- Dosya adlari kaynaga izlenebilir sekilde korunacak
- Ilk asamada 10 gorsel uzerinden tutarlilik kontrolu yapilacak

## Sonraki Adim
- Uygun proje/komut akisini secip toplu isleme pipeline'i calistir
