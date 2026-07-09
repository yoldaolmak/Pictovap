# 🗺 Pictova Roadmap

Pictova, içerik odaklı görsel otomasyonunda endüstri standardı olmayı hedefler. Geliştirme yol haritamız, uygulamayı **Premium bir SaaS** ve güçlü bir CLI/API ekosistemine dönüştürmek üzerine kuruludur.

---

## 🎯 Phase 1: Core Intelligence & Native Engine (Q3)
**Hedef:** Temel görsel arama, işleme ve AI-Destekli Metadata motorunun kusursuzlaştırılması.

- [x] **Native Engine Geçişi:** Legacy kodların bırakılıp, modüler (`attach`, `process`, `plan`) mimariye geçilmesi.
- [x] **Heading-Aware Selection:** Yazı içi H2/H3 başlıklarına duyarlı görsel atama ve SEO (slug/title) isimlendirme mekanizması.
- [x] **Vision Chain:** Gemini / Claude / Codex fallback yapısıyla resim piksellerinden kusursuz, anadilinde (TR) alt metin/başlık üretimi.
- [ ] **Multi-Source Fallback:** Semantic Selector başarısız olduğunda otomatik olarak Unsplash API'sine düşme (fallback).

---

## 🚀 Phase 2: Premium Features & Stock Integrations (Q4)
**Hedef:** Ticari (lisanslı) stok sitelerinin entegrasyonu ve kalite standartlarının artırılması.

- [ ] **Pictova Depot (DepositPhotos API):** Semantic search veya Unsplash yetersiz kaldığında lisanslı stok kütüphanelerinden otomatik satın alım ve indirme.
- [ ] **Advanced Quality Gate:** İndirilen resimlerde bulanıklık (blur), çözünürlük veya içerik kalitesi tespiti yaparak düşük kaliteli resimleri eleme sistemi.
- [ ] **WebP Optimization V2:** %100 kayıpsız (lossless) sıkıştırma algoritmalarının entegrasyonu ve EXIF verilerinin tam kontrolü.

---

## 🌐 Phase 3: Platform & UI/UX (Next Year)
**Hedef:** Geliştirici odaklı (CLI) araçtan, son kullanıcıya hitap eden yönetilebilir bir servise dönüşüm.

- [ ] **Meridyen UI Entegrasyonu:** YOOS-APP (İçerik üretim platformu) ile doğrudan görsel iletişim sağlayan web arayüzü.
- [ ] **Job Queue & Persisted Store:** Uzun süren attach görevlerini asenkron yönetmek için Redis / SQLite tabanlı görev kuyruğu (Task Queue).
- [ ] **Custom Prompts:** Kullanıcıların Vision Chain için kendi `system_prompt` yapılarını tanımlayabilmesi (Örn: Sadece teknik terimlerle açıklama yap).

---

> *"The road to seamless visual content is automated, intelligent, and context-aware."*
