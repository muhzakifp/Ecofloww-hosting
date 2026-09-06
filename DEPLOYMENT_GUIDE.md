# DEPLOYMENT GUIDE - EcoFlow AI

Panduan deployment secure untuk production di Railway (Backend) dan Vercel (Frontend).

---

## PRE-DEPLOYMENT CHECKLIST

- [ ] Review SECURITY_REVIEW_REPORT.md
- [ ] Backup database production
- [ ] Firebase credentials baru sudah digenerate (rotate dari yang lama)
- [ ] Environment variables sudah disiapkan
- [ ] Code review & testing selesai

---

## PART 1: BACKEND DEPLOYMENT (Railway)

### Step 1: Setup Environment Variables

Login ke Railway dashboard, pilih service backend, masuk ke Variables tab:

```bash
# === REQUIRED ===
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:port/dbname
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
SECRET_KEY=<generate-dengan: openssl rand -base64 32>

# === SECURITY ===
CORS_ORIGINS=https://your-frontend-app.vercel.app
ALLOWED_HOSTS=your-backend.up.railway.app
ADMIN_UIDS=firebase_uid_admin_1,firebase_uid_admin_2

# === OPTIONAL (Recommended) ===
REDIS_URL=redis://:password@host:port
RATE_LIMIT=100
RATE_LIMIT_WINDOW=60
IOT_API_KEY=<generate-random-string>

# === NEVER SET IN PRODUCTION ===
# ALLOW_DEV_AUTH=true  # ❌ JANGAN!
```

⚠️ **PENTING:**
- `ENVIRONMENT=production` wajib di-set untuk disable dev mode
- `ALLOW_DEV_AUTH` TIDAK BOLEH di-set di production
- `SECRET_KEY` harus random, minimal 32 karakter

### Step 2: Upload Firebase Credentials

Karena Railway tidak support upload file binary, ada 2 opsi:

**Opsi A: Base64 Encode (Recommended)**

```bash
# Di local machine:
cd backend/
cat firebase-credentials.json | base64

# Copy output, lalu tambahkan ke Railway variables:
FIREBASE_CREDENTIALS_BASE64=<paste-base64-string>
```

Lalu update `app/core/firebase.py`:

```python
import base64
import json

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            # Try base64 env var first
            cred_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")
            if cred_base64:
                cred_json = json.loads(base64.b64decode(cred_base64))
                cred = credentials.Certificate(cred_json)
            elif os.path.exists(FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            else:
                return False
            
            firebase_admin.initialize_app(cred)
            return True
    except Exception as e:
        logger.error(f"Firebase init failed: {e}")
        return False
```

**Opsi B: Mount as File**

Upload via Railway CLI atau commit file ke private repo (pastikan .gitignore tidak ignore file ini).

### Step 3: Run Database Migration

```bash
# SSH ke Railway container atau run locally dengan production DB
cd backend/
alembic upgrade head

# Verify migration
alembic current
# Output: abc123def456 (head) - add audit logs table
```

### Step 4: Verify Deployment

```bash
# Health check
curl https://your-backend.up.railway.app/health
# Output: {"status":"healthy"}

# Verify Firebase (harus 503 jika tidak ada token)
curl https://your-backend.up.railway.app/api/v1/batches
# Output: {"detail":"Unauthorized"} atau 401
```

⚠️ **JANGAN test dengan ALLOW_DEV_AUTH=true di production!**

---

## PART 2: FRONTEND DEPLOYMENT (Vercel)

### Step 1: Generate New Firebase Config

1. Login ke Firebase Console
2. Project Settings → General → Your apps → Add app (Web)
3. Copy new config (API key berbeda dari yang leaked)

### Step 2: Setup Environment Variables di Vercel

Dashboard Vercel → Project → Settings → Environment Variables:

```bash
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy... (NEW KEY)
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app/
```

⚠️ **PENTING:**
- Gunakan `https://` bukan `http://` untuk API_URL
- Pastikan URL backend tidak ada trailing slash ganda

### Step 3: Update CORS di Backend

Setelah deploy Vercel, copy URL frontend (misal: `https://ecoflow-ai.vercel.app`)

Update Railway env var:

```bash
CORS_ORIGINS=https://ecoflow-ai.vercel.app
```

Restart backend service di Railway.

### Step 4: Test Integration

1. Buka `https://ecoflow-ai.vercel.app/login`
2. Sign up dengan email baru
3. Create batch baru
4. Buka incognito/private window
5. Sign up dengan email berbeda
6. Verify TIDAK melihat batch user pertama ✅

---

## PART 3: SECURITY POST-DEPLOYMENT

### Firebase Security Rules

Update Firestore rules (jika menggunakan Firestore):

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

Update Storage rules:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /users/{userId}/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### Monitoring & Alerts

1. **Railway Logs:**
   ```bash
   railway logs --follow
   ```

2. **Watch for Errors:**
   ```bash
   # Grep untuk "ERROR" atau "CRITICAL"
   railway logs | grep -i "error\|critical"
   ```

3. **Audit Log Queries:**
   ```sql
   -- Top 10 actions hari ini
   SELECT action, COUNT(*) as count 
   FROM audit_logs 
   WHERE created_at > NOW() - INTERVAL '1 day' 
   GROUP BY action 
   ORDER BY count DESC 
   LIMIT 10;

   -- Failed login attempts
   SELECT user_id, ip_address, created_at 
   FROM audit_logs 
   WHERE action = 'LOGIN' AND status = 'failed' 
   ORDER BY created_at DESC 
   LIMIT 20;
   ```

---

## PART 4: ROLLBACK PLAN

### Jika Ada Masalah Setelah Deploy

1. **Rollback Railway:**
   ```bash
   railway rollback
   ```

2. **Rollback Vercel:**
   Dashboard → Deployments → Previous deployment → Promote to Production

3. **Rollback Database Migration:**
   ```bash
   cd backend/
   alembic downgrade -1  # Rollback 1 migration
   # Atau specific revision:
   alembic downgrade <previous_revision_id>
   ```

4. **Restore Database Backup:**
   ```bash
   pg_restore -d ecoflow_db backup.dump
   ```

---

## PART 5: TROUBLESHOOTING

### Issue: "503 Service Unavailable" di semua endpoint

**Cause:** Firebase tidak terinisialisasi

**Fix:**
1. Check `FIREBASE_CREDENTIALS_BASE64` atau file path
2. Verify format JSON credentials benar
3. Check Railway logs: `railway logs | grep Firebase`

### Issue: User bisa melihat data user lain

**Cause:** `ALLOW_DEV_AUTH=true` masih aktif atau `ENVIRONMENT` tidak di-set

**Fix:**
```bash
# Hapus ALLOW_DEV_AUTH dari Railway variables
# Set ENVIRONMENT=production
# Restart service
```

### Issue: CORS error di browser

**Cause:** Frontend URL tidak di whitelist

**Fix:**
```bash
# Update Railway variable:
CORS_ORIGINS=https://your-exact-vercel-url.vercel.app

# Restart backend
```

### Issue: Rate limit too aggressive

**Cause:** In-memory rate limiter tidak sync antar instances

**Fix:**
```bash
# Setup Redis di Railway
# Add Redis add-on
# Set REDIS_URL variable
# Restart service
```

### Issue: IoT webhook return 401

**Cause:** API key tidak match

**Fix:**
```bash
# Generate new key:
openssl rand -hex 32

# Update Railway:
IOT_API_KEY=<new-key>

# Update IoT device config dengan key yang sama
```

---

## PART 6: PERFORMANCE OPTIMIZATION

### Database Connection Pooling

Update `backend/app/core/database.py`:

```python
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=10,          # Default 5
        max_overflow=20,       # Default 10
        pool_pre_ping=True,    # Verify connections
        pool_recycle=3600      # Recycle after 1 hour
    )
```

### Redis Configuration

```bash
# Railway Redis optimal config
REDIS_URL=redis://:password@host:port/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### CDN for Static Assets

Vercel automatic edge CDN sudah optimal, tapi bisa tambahkan:

```javascript
// next.config.ts
module.exports = {
  images: {
    domains: ['firebasestorage.googleapis.com'],
    formats: ['image/avif', 'image/webp'],
  },
  compress: true,
  poweredByHeader: false,
}
```

---

## VERIFICATION CHECKLIST

Setelah deployment, verify:

- [ ] Health endpoint return 200: `/health`
- [ ] Unauthorized access return 401: `/api/v1/batches` (tanpa token)
- [ ] Login berhasil dengan Firebase
- [ ] Multi-user isolation berfungsi (2 user berbeda tidak melihat data satu sama lain)
- [ ] Batch CRUD operations berfungsi
- [ ] Audit logs tercatat di database
- [ ] CORS tidak error di browser
- [ ] Rate limiting berfungsi (test dengan > 60 req/min)
- [ ] IoT webhook require API key (return 401 tanpa header `X-API-Key`)
- [ ] Admin role escalation tercatat di audit log

---

## SUPPORT & MAINTENANCE

### Regular Tasks

**Daily:**
- Monitor Railway logs untuk errors
- Check database size growth

**Weekly:**
- Review audit logs untuk suspicious activity
- Check rate limit metrics
- Verify backup berjalan

**Monthly:**
- Rotate IoT API keys
- Review Firebase auth logs
- Update dependencies (`npm audit`, `pip-audit`)

### Emergency Contacts

```
Backend Issues: Check Railway logs & status page
Frontend Issues: Check Vercel logs & deployment status
Database Issues: Check Railway PostgreSQL metrics
Firebase Issues: Check Firebase Console status
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-06  
**Next Review:** 2026-10-06
