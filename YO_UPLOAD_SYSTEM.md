# YO OS — Image Upload & Processing System

**Status:** ✅ Production Ready (Apr 5, 2026)

---

## 🎯 Overview

Complete, automated image processing + WordPress upload pipeline:

```
User command: "5 foto yo 21312"
    ↓
[1] Load 5 most recent images from ~/Downloads/
[2] Crop (1200x750 landscape | 1920x1200 portrait)
[3] Apply YO Blue/Teal filter + auto saturation
[4] Clean EXIF metadata
[5] Generate semantic metadata (Vision API)
[6] Export WebP (%80 quality)
[7] Upload to WordPress REST API
[8] Attach to post ID (featured_media=false)
    ↓
User edits post: "Insert images into paragraphs"
```

---

## 📦 Components

### 1. **yo_image_processor.py**
- Image loading, cropping (center crop to 16:10)
- YO Blue/Teal filter pipeline
- Automatic saturation analysis (+/- per image)
- EXIF removal
- WebP export

**Filter Spec:**
```
- Blue channel boost: +8%
- Contrast: +10%
- Saturation: +8% (±adjustment per image)
- Brightness: +5% (airy premium feel)
- Sharpness: +1.5x (editorial clarity)
```

### 2. **yo_metadata_generator.py**
- Claude Vision API analysis
- Semantic alt/title/caption/description
- SEO-friendly metadata
- Fallback: basic metadata if API unavailable

**Metadata Fields:**
```json
{
  "what": "one-liner description",
  "alt": "petra-antik-kenti (max 125 chars)",
  "title": "Petra Antik Kenti El Hazne (max 60 chars)",
  "caption": "Short caption (max 150 chars)",
  "description": "Long description (max 300 chars)",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}
```

### 3. **yo_wp_uploader.py**
- WordPress REST API integration
- Media upload (WebP)
- Metadata attachment (alt/title/caption/description)
- Attach to post (not featured image)

**Supported Sites:**
- yoldaolmak.com (default)
- gezievreni.com
- gezgindunyasi.com

### 4. **yo_orchestrator.py**
- Command parser: `"5 foto yo 21312"` → parameters
- Pipeline orchestration
- Logging & error handling

### 5. **yo_cli.sh**
- User-friendly CLI wrapper

---

## 🚀 Usage

### Command Format

```bash
# Basic
"5 foto yo 21312"

# With site
"3 foto yo 21312 gezievreni"

# Single image
"1 foto yo 50000"
```

**Interpretation:**
- `5` = take 5 most recent images from ~/Downloads/
- `foto yo` = literal command string
- `21312` = target post ID
- `gezievreni` (optional) = target site (default: yoldaolmak)

### Examples

```bash
# 5 images → yoldaolmak post 21312
python3 yo_orchestrator.py "5 foto yo 21312"

# 3 images → gezievreni post 12345
python3 yo_orchestrator.py "3 foto yo 12345 gezievreni"

# 1 image
python3 yo_orchestrator.py "1 foto yo 50000"
```

---

## ✅ Latest Operational Rules (Apr 2026)

- Kaynak klasor verildiginde secim sadece o klasorden yapilir (HDD/Mac Photos karistirilmaz).
- H2/H3 basliklari dosya adina birebir yazilmaz; sadece uygun gorsel secimi icin sinyal olarak kullanilir.
- Rename semantik olmalidir: `alacati-sokak-gorunumu.webp`, `alacati-degirmenleri.webp` gibi.
- Dosya adi 5-6 kelimeyi asmamali, anlamsiz `-2/-3` veya `genel` turu isimler olusmamalidir.
- EXIF orientation normalize edilir (yan/dik donme hatalari engellenir).
- Final gorsellerde canlilik/kontrast dengesi korunur, evrensel house-style uygulanir.
- Metadata (Title/Description/Caption/Keywords) her dosyaya embed edilir; bos alan birakilmaz.
- Google Vision sadece free-kota modunda semantic dogrulama/etiketleme amacli kullanilir.

---

## 🔧 Setup & Requirements

### Python Dependencies
```bash
pip install Pillow anthropic requests
```

### Environment Variables
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

If not set: falls back to basic metadata (alt, title, caption, description generated from filename).

### WordPress Credentials
Stored in `yo_orchestrator.py` under `SITE_ENDPOINTS`:
- yoldaolmak.com: ✓ configured
- gezievreni.com: TODO (add credentials)
- gezgindunyasi.com: TODO (add credentials)

---

## 📊 Output

### Directory Structure
```
/tmp/yo_upload_work/
├── kalenderis_yo.webp           # processed image
└── yo_upload_20260405_131657.json    # execution log
```

### Log File Format
```json
{
  "command": "5 foto yo 21312",
  "site": "yoldaolmak",
  "post_id": 21312,
  "status": "success",
  "uploaded_count": 5,
  "failed_count": 0,
  "steps": {
    "images_loaded": { ... },
    "images_processed": { ... },
    "metadata_generated": { ... },
    "upload_complete": { ... }
  }
}
```

---

## 🎨 Filter Details

**YO Blue/Teal Filter** — Modern, cinematic, NatGeo/Vogue editorial style

**Design Goals:**
- ✓ Consistent visual signature across all images
- ✓ Premium, contemporary look (not warm/vintage)
- ✓ Works on color + B&W photos
- ✓ 2026 trend-aligned (cool tones, high contrast)

**Technical Implementation:**
1. Blue channel enhancement (teal shadows)
2. Contrast boost (+10%)
3. Selective saturation (+8% base, ±adjustment per image)
4. Brightness lift (+5%, airy premium feel)
5. Unsharp mask (editorial clarity)
6. EXIF complete removal

---

## 📝 Metadata Generation

### Vision API Analysis
Claude Vision API analyzes each image:
- **What**: one-liner description
- **Context**: location, composition, subject
- **SEO optimization**: keywords, semantic structure

### Fallback (No API)
If `ANTHROPIC_API_KEY` not set:
```python
{
  "alt": "filename-slugified",
  "title": "Filename Title Case",
  "caption": "Image",
  "description": "Uploaded image"
}
```

---

## 🐛 Troubleshooting

### Upload fails: "500 Server Error"
→ Check WordPress uploads folder permissions:
```bash
ssh -p 1144 root@yoldaolmak.com
chown -R yoldaolmak:yoldaolmak /home/yoldaolmak/public_html/wp-content/uploads/
chmod -R 755 /home/yoldaolmak/public_html/wp-content/uploads/
```

### Metadata generation fails
→ Check API key: `echo $ANTHROPIC_API_KEY`
→ If not set, system falls back to basic metadata automatically

### Image not found in Downloads
→ Ensure file extension is recognized (.jpg, .png, .webp, .gif)
→ Check file modification time (uses `mtime` for sorting)

---

## 📈 Roadmap

- [ ] Interactive image selection (skip specific images)
- [ ] Custom saturation overrides per image
- [ ] Batch metadata review before upload
- [ ] Archive processed images
- [ ] Integration with VIL core (visual memory index)
- [ ] Deposit Photos fallback for missing images
- [ ] Post content auto-insertion (image → paragraph)
- [ ] Future: H3-level image matching and placement with section scoring, hero conflict rules, and duplicate-scene penalties

---

## 📚 Architecture Integration

Part of **YO OS Visual Intelligence Layer (VIL)**:

```
[Visual Memory Index] → [Asset Selection] → [Image Processing] → [WordPress Publish]
                                                 ↑
                                         (This System)
```

---

## 🤝 Credits

- **Filter Design:** Modern cinematic Blue/Teal grade
- **Metadata:** Claude 3.5 Sonnet Vision API
- **Processing:** PIL (Pillow)
- **WordPress:** REST API v2
- **Architecture:** YO OS Editorial System

---

**Last Updated:** Apr 5, 2026
**Status:** Production Ready ✅
