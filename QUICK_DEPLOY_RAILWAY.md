# 🚀 QUICK DEPLOY TO RAILWAY - CORS FIX

**Last Updated:** 2026-09-06  
**Status:** ✅ Code ready, awaiting Railway deployment

---

## ⚡ QUICK STEPS (5 Minutes)

### 1️⃣ Railway Dashboard
Login: https://railway.app/dashboard

### 2️⃣ Set Environment Variables
Go to: **Your Project → Backend Service → Variables**

**ADD THESE TWO VARIABLES:**

```bash
CORS_ORIGINS=https://ecoflow-hosting.vercel.app
```

```bash
ALLOWED_HOSTS=ecoflow-hosting-production.up.railway.app,*.up.railway.app
```

### 3️⃣ Deploy
Railway will auto-deploy from GitHub (if connected)

**OR Manual Deploy:**
- Click **"Deploy"** button in Railway Dashboard
- OR: `railway up` (if using Railway CLI)

### 4️⃣ Restart Service (if needed)
Settings → **Restart**

### 5️⃣ Test
```bash
curl -X OPTIONS https://ecoflow-hosting-production.up.railway.app/api/v1/batches \
  -H "Origin: https://ecoflow-hosting.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Expected:** `HTTP/2 200` with CORS headers

---

## ✅ VERIFICATION CHECKLIST

After deployment, verify:

- [ ] Railway logs show deployment success
- [ ] Environment variables are set correctly
- [ ] OPTIONS request returns 200 (not 400)
- [ ] CORS headers present in OPTIONS response
- [ ] Frontend Vercel can load data (no CORS errors)
- [ ] Browser console has no errors

---

## 🔍 VERIFY ENVIRONMENT VARIABLES

### Via Railway Dashboard:
1. Project → Backend Service
2. Variables tab
3. Check `CORS_ORIGINS` and `ALLOWED_HOSTS` are set

### Via Railway CLI:
```bash
railway variables list | grep -E "CORS|ALLOWED"
```

**Expected Output:**
```
CORS_ORIGINS=https://ecoflow-hosting.vercel.app
ALLOWED_HOSTS=ecoflow-hosting-production.up.railway.app,*.up.railway.app
```

---

## 🧪 TESTING COMMANDS

### Test 1: Health Check
```bash
curl https://ecoflow-hosting-production.up.railway.app/health
```
**Expected:** `{"status":"healthy"}`

### Test 2: CORS Preflight
```bash
curl -X OPTIONS \
  https://ecoflow-hosting-production.up.railway.app/api/v1/batches \
  -H "Origin: https://ecoflow-hosting.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  -v
```

**Expected Headers:**
```
< HTTP/2 200
< access-control-allow-origin: https://ecoflow-hosting.vercel.app
< access-control-allow-methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
< access-control-allow-headers: *
< access-control-allow-credentials: true
```

### Test 3: From Browser
1. Open: https://ecoflow-hosting.vercel.app
2. Open DevTools → Console
3. Look for errors
4. ✅ Should see: No CORS errors
5. ✅ Should see: API requests succeed

---

## 🔧 TROUBLESHOOTING

### Issue: Still getting 400 for OPTIONS

**Check:**
```bash
railway logs | grep OPTIONS
```

**Solutions:**
1. Verify `ALLOWED_HOSTS` variable is set
2. Restart Railway service
3. Check for typos in environment variables
4. Verify GitHub auto-deploy completed

### Issue: CORS error persists

**Check:**
```bash
railway variables list | grep CORS_ORIGINS
```

**Solutions:**
1. Verify `CORS_ORIGINS` includes exact Vercel URL
2. Ensure no trailing slash in URL
3. Use `https://` not `http://`
4. Clear browser cache (Ctrl+Shift+R)

### Issue: Deployment not triggered

**Solutions:**
1. Check Railway → Deployments tab
2. Manually trigger: Click "Deploy" button
3. Or use: `railway up`
4. Check GitHub webhook is connected

---

## 📊 EXPECTED RAILWAY LOGS

### Before Fix (❌ ERROR):
```
2026-09-06 13:00:00 | OPTIONS /api/v1/batches -> 400
2026-09-06 13:00:01 | OPTIONS /api/v1/users/me -> 400
```

### After Fix (✅ SUCCESS):
```
2026-09-06 13:45:00 | OPTIONS /api/v1/batches -> 200
2026-09-06 13:45:00 | GET /api/v1/batches -> 200
2026-09-06 13:45:01 | OPTIONS /api/v1/users/me -> 200
2026-09-06 13:45:01 | GET /api/v1/users/me -> 200
```

---

## 🎯 SUCCESS INDICATORS

### Railway Dashboard:
✅ Deployment status: Success  
✅ Service status: Active  
✅ Logs show: 200 for OPTIONS requests

### Browser (Vercel Frontend):
✅ No CORS errors in console  
✅ Network tab shows: OPTIONS → 200  
✅ Network tab shows: GET/POST → 200  
✅ Data loads successfully

### curl Test:
✅ OPTIONS returns 200  
✅ CORS headers present  
✅ `access-control-allow-origin` matches Vercel URL

---

## 📞 NEED HELP?

### View Logs:
```bash
railway logs --follow
```

### Check Variables:
```bash
railway variables list
```

### Restart Service:
```bash
railway restart
```

### Re-deploy:
```bash
railway up
```

---

## 🔗 IMPORTANT LINKS

- **GitHub Repo:** https://github.com/muhzakifp/Ecofloww-hosting.git
- **Railway Dashboard:** https://railway.app/dashboard
- **Vercel Frontend:** https://ecoflow-hosting.vercel.app
- **Backend API:** https://ecoflow-hosting-production.up.railway.app
- **API Docs:** https://ecoflow-hosting-production.up.railway.app/docs

---

## 📄 RELATED DOCUMENTATION

- **Full Fix Documentation:** `CORS_FIX_DOCUMENTATION.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`
- **Security Review:** `SECURITY_REVIEW_REPORT.md`

---

**Ready to deploy?** Follow steps 1-5 above! 🚀
