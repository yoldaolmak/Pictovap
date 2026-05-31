# Pillar Yapım Protokolü

Bu dosya, bu oturumda uygulanan yöntemi kalıcı hale getirmek için yazıldı. Amaç, bir sonraki pillar sayfasında aynı kaliteyi, aynı dili ve aynı yerleşim mantığını tekrar kurmak.

## 1. Başlangıç Mantığı

1. Önce kullanıcıdan gelen örnek modeli temel al.
2. Sonra hedef sayfanın mevcut yapısını tara.
3. İçerikleri tek tek ayır:
   - karar veren ana bölüm
   - temel okunacak yazılar
   - tüm rehberler
   - yazı içi kartlar
   - destekleyici açıklama blokları
4. Her bölümü aynı tasarım gibi değil, aynı görev gibi düşün.

## 2. İçerik Önceliği

- Kullanıcı hangi sayfaları verdiyse onları tarayıp referans kabul et.
- Ana hedef, örnek modeldeki dili ve yoğunluğu yakalamak.
- Yeni pillar üretirken sadece “güzel görünme” hedefi yok; sayfanın karar vermeyi kolaylaştırması gerekir.
- Gereksiz tekrarları temizle, ama ana bilgi omurgasını koru.

## 3. Dil Standardı

- Türkçe doğal, net ve kullanıcıya dönük olmalı.
- Cümleler kısa ama yüzeysel olmamalı.
- Ton, rehber dili gibi olmalı:
  - doğrudan
  - pratik
  - iddiasız
  - ama güven veren
- Aynı fikri farklı cümlelerle tekrar etmekten kaçın.
- Başlıklar ile metinler aynı seviyede konuşmalı; başlık güçlü ise alt metin de onu taşımalı.

## 4. Bölüm Kuralları

### Karar Omurgası

- İlk bölüm, okuyucunun ana sorusunu netleştirmeli.
- Bu bölümde hedef, “neye bakmalıyım?” sorusuna yön vermek.
- Omurga bloğu, pilların ana mantığını kurar.

### Bilet Almadan Önce Okunacak Temel Yazılar

- Bu bölümün kart yapısına dokunma.
- Yatay spoke düzeni burada korunmalı.
- Bu blok, ana karar öncesi temel okumalar için ayrı ve sabit kalmalı.
- Kullanım amacı bilgi yoğunluğu değil, yönlendirme.

### Tüm Uçak Bileti Rehberleri

- Bu bölümde spoke kart tasarımı şu yapıda kullanılmalı:

```html
class="yo-card-grid yo-card-grid--3 yo2-grid yo-home-spoke-grid"
```

- Bu yapı, tüm rehberleri daha dengeli ve okunur gösterir.
- Bu bölüm, geniş bir rehber listesini ana kategori sayfasında toplamak için uygundur.

### Post İçi Kartlar

- Yazı içindeki kartlar alan kazanmak için yatay ve dar kullanılmalı.
- Amaç büyük bloklar yaratmak değil, metin akışını kesmeden bağlantı vermek.
- Post içi kartlar, sayfayı ağırlaştırmadan okuyucuyu bir alt konuya taşır.

## 5. Tasarım Kararları

- Bölümün görevi neyse, kart tipi ona göre seçilmeli.
- Her yerde aynı kart düzeni kullanılmaz.
- Temel ayrım:
  - ana rehber listesi için daha geniş spoke grid
  - temel okumalar için yatay spoke kart
  - içerik içi yönlendirme için dar yatay kart
- Bir bölümün düzeni değişirken diğer bölümün amacı bozulmamalı.

## 6. Çalışma Sırası

1. Örnek modeli oku.
2. Hedef sayfanın mevcut dosyasını tara.
3. Bölümleri ayıkla.
4. Hangi blokların sabit kalacağını belirle.
5. Hangi blokların yeni grid ya da yeni metin alacağını belirle.
6. İçeriği yaz.
7. Kart düzenini uygula.
8. HTML/PHP yapısını bozmadan dosyayı güncelle.
9. Sadece gerekli doğrulamayı yap.

## 7. Test Disiplini

- Staging üzerinde ana amaç, yapısal doğrulama yapmaktır.
- Fazla test yapıp oturumu uzatma.
- Kullanıcı “bu kadar test yeterli” dediğinde staging tarafında dur.
- Production’a geçince asıl kontrol yapılır.
- Yani test stratejisi:
  - staging = hızlı ve yeterli doğrulama
  - production = gerçek son kontrol

## 8. Uygulama İlkeleri

- Bir bölümün sınıfı veya grid tipi değişiyorsa, yalnız o bölümün kapsamını değiştir.
- Komşu bölümlere dokunma.
- Özellikle konuşulmuş bir yatay spoke alan varsa onu koru.
- Metin değişikliği ile yerleşim değişikliğini birbirine karıştırma.
- Gözden kaçabilecek sınıf değişikliklerini küçük ve kontrollü yap.

## 9. Bu Oturumdan Kalan Net Kural

- `Bilet Almadan Önce Okunacak Temel Yazılar` yatay spoke kart olarak kalır
- `Tüm Uçak Bileti Rehberleri` bölümü `yo-card-grid yo-card-grid--3 yo2-grid yo-home-spoke-grid` yapısına geçer
- Post içi kartlar dar ve yatay kalır
- Staging’de temel doğrulama yeterlidir
- Production’da son test yapılır

## 10. Sonuç

Bu yaklaşımın hedefi, her pillar’da aynı editoryal kaliteyi ve aynı görsel disiplini tekrar etmek. Yeni sayfa hazırlanırken bu dosya referans alınmalı; önce yapı, sonra metin, sonra kart düzeni, en son da kısıtlı test.

## 11. Oturum Açılış Akışı

- Oturum başlarken önce bu dosyayı oku.
- Ardından gerekli proje dizinine geç.
- Varsayılan çalışma klasörü:
  - `/Users/KemalKaya/YO_OS_VIL`
- Eğer görev WordPress staging/prod tarafını etkiliyorsa önce mevcut durumu tara.
- Staging ve production ayrımını net tut.
- Dosya, tema, CSS veya PHP değişikliği gerekiyorsa önce etki alanını daralt.
- Gereksiz test veya gereksiz yayın adımı açma.

## 12. Server Bağlantı Kuralı

- Bu projede uzak sunucuya bağlanmak gerektiğinde kullanılacak temel SSH kalıbı:

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p 1144 root@37.148.213.185
```

- Staging dosya yolu:
  - `/home/virtfs/yoldaolmak/home/yoldaolmak/public_html/staging.yoldaolmak.com`
- Production tarafında işlem yapmadan önce staging doğrulaması tamamlanmalı.
- Sunucuya dosya kopyalama gerekiyorsa önce yerelde değişikliği bitir, sonra upload et.
- PHP dosyalarında önce syntax kontrolü, sonra sınırlı doğrulama yapılır.

## 13. Auto Mod ve İzin Kuralı

- Auto modda mümkün olan her şeyi önce kendim çözmeye çalışırım.
- Aşağıdaki durumlarda kullanıcı izni isterim:
  - production’a geçiş
  - sunucuda kalıcı değişiklik
  - dış dünyaya etkisi olan yayın işlemi
  - riskli komutlar
  - yıkıcı işlem ihtimali
- İzin isterken kısa, net ve tek adımlı sorarım.
- Kullanıcı “devam et” derse akışı sürdürürüm.
- Kullanıcı “dur” derse bulunduğum noktayı özetleyip beklerim.

## 14. Başlangıçta İzlenecek Sıra

1. `pillar.md` oku.
2. Gerekli ise mevcut çalışma notlarını tara.
3. Hedef dosyayı bul.
4. Yerel değişikliği hazırla.
5. Staging’e uygula.
6. Sadece gerekli doğrulamayı yap.
7. Production istenirse kullanıcı onayı al.
8. Onaydan sonra üretim adımını yap.
