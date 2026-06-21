# VIL - Güvenlik Best Practices

Bu doküman, VIL (Visual Intelligence Layer) platformunda güvenlik best practices'i açıklar.

## Hassas Bilgilerin Yönetimi

### Environment Variables

Tüm hassas bilgiler `.env` dosyasında tutulmalıdır. Bu dosya asla git'e commit edilmemelidir.

**.env.example:**
```bash
# API Keys
GOOGLE_CLOUD_VISION_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# WordPress Credentials
WP_USER=hamal
WP_PASSWORD=app-password-here

# Database
DATABASE_URL=postgresql://user:pass@localhost/vil_db
```

**.gitignore'da mutlaka bulunsun:**
```
.env
.env.local
.env.*.local
*.db
logs/
tmp/
```

### API Key Rotasyonu

API key'leri düzenli olarak rotate edilmelidir:

- **Google Cloud Vision**: Her 90 günde bir
- **WordPress App Password**: Her 6 ayda bir
- **Anthropic API**: Her yıl bir

## SQL Injection Önleme

### ❌ Yanlış Kullanım

```python
# ASLA BUNU YAPMA
query = f"SELECT * FROM images WHERE path = '{user_input}'"
cursor.execute(query)
```

### ✅ Doğru Kullanım

```python
# Prepared statements kullan
query = "SELECT * FROM images WHERE path = ?"
cursor.execute(query, (user_input,))
```

VIL'de tüm database sorguları parameterized query kullanır.

## Input Validation

### User Input Sanitization

Tüm kullanıcı inputları validate ve sanitize edilmelidir:

```python
from pathlib import Path

def safe_path(user_input: str) -> Path:
    """Kullanıcı input'unu güvenli path'e çevir"""
    # Sadece alphanumeric ve temel karakterlere izin ver
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', user_input)
    
    # Path traversal engelle
    if '..' in sanitized or sanitized.startswith('/'):
        raise ValueError("Invalid path")
    
    return Path(sanitized)
```

### POST ID Validation

```python
def validate_post_id(post_id: str) -> int:
    """POST ID'nin geçerli integer olduğundan emin ol"""
    try:
        pid = int(post_id)
        if pid <= 0:
            raise ValueError("POST ID must be positive")
        return pid
    except (ValueError, TypeError):
        raise ValueError(f"Invalid POST ID: {post_id}")
```

## Rate Limiting

### API Call Throttling

External API'lerde rate limiting uygulanmalıdır:

```python
import time
from functools import wraps

def rate_limit(calls_per_minute: int):
    """API çağrılarını throttle et"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls_per_minute=60)  # Dakikada 60 çağrı
def call_vision_api(image_path: str):
    # Google Vision API çağrısı
    pass
```

### WordPress API Rate Limiting

WordPress REST API için:

```python
class WPRateLimiter:
    def __init__(self, requests_per_second: float = 2.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0
        
    def wait_if_needed(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
```

## Error Handling & Logging

### Sensitive Information Masking

Loglarda hassas bilgiler maskelenmelidir:

```python
import re

def mask_sensitive_info(log_message: str) -> str:
    """API key, password gibi bilgileri maskele"""
    # API key pattern
    log_message = re.sub(
        r'(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9]{20,})["\']?',
        r'\1=****REDACTED****',
        log_message,
        flags=re.IGNORECASE
    )
    
    # Password pattern
    log_message = re.sub(
        r'(password|passwd|pwd)\s*[=:]\s*["\']?([^"\',\s]+)["\']?',
        r'\1=****REDACTED****',
        log_message,
        flags=re.IGNORECASE
    )
    
    return log_message
```

### Exception Handling

```python
try:
    result = process_image(image_path)
except FileNotFoundError as e:
    logger.error(f"Image not found: {mask_sensitive_info(str(e))}")
except requests.exceptions.RequestException as e:
    logger.error(f"API request failed: {mask_sensitive_info(str(e))}")
except Exception as e:
    logger.critical(f"Unexpected error: {mask_sensitive_info(str(e))}")
    raise
```

## File System Security

### Path Traversal Prevention

```python
from pathlib import Path

def safe_join(base_dir: Path, user_path: str) -> Path:
    """Path traversal saldırılarını engelle"""
    base_dir = base_dir.resolve()
    full_path = (base_dir / user_path).resolve()
    
    # full_path, base_dir içinde mi?
    try:
        full_path.relative_to(base_dir)
        return full_path
    except ValueError:
        raise ValueError("Path traversal attempt detected")
```

### File Permissions

VIL dizini için önerilen permissions:

```bash
# Dizin permissions
chmod 755 /path/to/vil

# Dosya permissions
chmod 644 /path/to/vil/*.py

# .env dosyası (daha kısıtlayıcı)
chmod 600 /path/to/vil/.env

# Owner ayarla
chown -R $USER:$USER /path/to/vil
```

## Network Security

### HTTPS Enforcement

Tüm WordPress bağlantıları HTTPS üzerinden olmalı:

```python
def validate_wordpress_url(url: str) -> str:
    """URL'in HTTPS olduğunu doğrula"""
    if not url.startswith('https://'):
        raise ValueError("WordPress URL must use HTTPS")
    return url
```

### SSL Certificate Verification

```python
import requests

session = requests.Session()
session.verify = True  # SSL cert verification aktif
session.mount('https://', requests.adapters.HTTPAdapter(
    max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
))
```

## Database Security

### Connection String Security

Database connection string'ler environment variable'dan okunmalı:

```python
# .env'den
DATABASE_URL = os.environ.get('DATABASE_URL')

# Connection
conn = psycopg2.connect(DATABASE_URL)
```

### Least Privilege Principle

Database kullanıcısı sadece gerekli permission'lara sahip olmalı:

```sql
-- Sadece gerekli permission'lar
GRANT SELECT, INSERT, UPDATE ON images TO vil_user;
GRANT SELECT ON visual_memory TO vil_user;

-- Asla verme
-- GRANT ALL PRIVILEGES TO vil_user;
-- GRANT DROP TO vil_user;
```

## Monitoring & Auditing

### Security Log Events

Aşağıdaki event'ler loglanmalı:

- Başarısız login denemeleri
- Invalid input attempts
- Rate limit violations
- Permission denied errors
- Unusual API usage patterns

```python
def log_security_event(event_type: str, details: dict):
    """Güvenlik event'ini logla"""
    logger.warning(
        f"SECURITY_EVENT: {event_type}",
        extra={
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': mask_sensitive_info(json.dumps(details))
        }
    )
```

### Regular Security Audits

- **Aylık**: Log review, unusual pattern detection
- **Üç aylık**: Dependency vulnerability scan
- **Yıllık**: Full security audit, penetration test

## Dependency Security

### Regular Updates

Bağımlılıkları düzenli güncelle:

```bash
# Güvenlik güncellemelerini kontrol et
pip list --outdated

# Güvenlik taraması yap
pip-audit

# Güncelle
pip install --upgrade -r requirements.txt
```

### Vulnerability Scanning

```bash
# pip-audit kurulumu
pip install pip-audit

# Tarama yap
pip-audit

# GitHub Actions ile otomatik tarama
# .github/workflows/security-scan.yml
```

## Incident Response

### Security Incident Plan

1. **Detect**: Anormal aktivite tespit et
2. **Contain**: Etkiyi sınırla (API keys'i revoke et vb.)
3. **Eradicate**: Kök nedeni bul ve düzelt
4. **Recover**: Sistemi normale döndür
5. **Learn**: Lessons learned dokümante et

### Emergency Contacts

- **Proje Lead**: Kemal
- **Security Team**: [security-email@example.com]
- **Incident Hotline**: [phone-number]

---

*Son Güncelleme: Haziran 2024*  
*Versiyon: 1.0*
