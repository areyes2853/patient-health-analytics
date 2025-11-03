# 🔑 Key Setup & Epic Registration Guide

## Where Your Keys Live

After running `python generate_keys.py`, you'll have:

```
patient-health-analytics/
├── keys/                      ← New folder created
│   ├── private_key.pem       ← KEEP SECRET! Never share!
│   └── public_key.pem        ← Upload this to Epic
├── epic_backend_auth.py
├── generate_keys.py
└── .env
```

## 📍 Step-by-Step Setup

### Step 1: Generate Keys on YOUR COMPUTER

Open Terminal/Command Prompt and run:

```bash
# Navigate to your project
cd /Users/angelminimac/Desktop/GA-project/code/ga/labs/-intro-to-mongoose-lab-/patient-health-analytics

# Generate the keys
python generate_keys.py
```

**Output will look like:**
```
Generating RSA key pair...
✓ Private key saved to: ./keys/private_key.pem
  ⚠️  Keep this file SECRET and secure!
✓ Public key saved to: ./keys/public_key.pem

============================================================
PUBLIC KEY (to register with Epic):
============================================================
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA...
[lots of random characters]
...
-----END PUBLIC KEY-----
```

### Step 2: Epic Sandbox Registration

#### Option A: Epic on FHIR Sandbox (Recommended for Testing)

1. **Go to Epic's Sandbox**: https://fhir.epic.com/

2. **Create Account** (if you don't have one)
   - Click "Sign Up"
   - Fill out the form
   - Verify your email

3. **Navigate to "Backend Services"**
   - Log into Epic on FHIR
   - Click on your profile/account
   - Look for "Build Apps" or "My Apps"
   - Select "Create New App"

4. **Choose App Type**
   - Select **"Backend Services"** (NOT "Patient Standalone" or "Provider Standalone")
   - This is the key difference!

5. **Fill Out App Details**
   ```
   Application Name: Patient Health Analytics Backend
   Application Type: Backend Services
   FHIR Version: R4
   Scopes Requested:
     ☑ system/Patient.read
     ☑ system/Observation.read
     ☑ system/*.read
   ```

6. **Upload Your Public Key**
   - Look for "Public Key" or "JWKS" upload section
   - Click "Upload" or "Add Public Key"
   - **Option 1**: Upload the file `keys/public_key.pem`
   - **Option 2**: Copy/paste the contents of `keys/public_key.pem`

7. **Submit & Get Client ID**
   - Click "Save" or "Submit"
   - Epic will give you a **Client ID** (looks like: `abc123-def456-ghi789`)
   - **SAVE THIS CLIENT ID!** You'll need it for your `.env` file

#### Option B: If Using Epic's Open.Epic Sandbox

1. Go to: https://open.epic.com/
2. Sign in or create account
3. Navigate to "Apps" → "Create App"
4. Choose "Backend Services"
5. Follow similar steps as above

### Step 3: Update Your .env File

Copy the Client ID from Epic and add it to your `.env`:

```bash
# Open your .env file
nano .env

# Or use any text editor
# Add this line:
EPIC_BACKEND_CLIENT_ID=your-client-id-from-epic-here
```

Your `.env` should look like:

```env
# Backend Services Configuration
EPIC_BACKEND_CLIENT_ID=abc123-def456-ghi789
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
EPIC_FHIR_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
PRIVATE_KEY_PATH=./keys/private_key.pem

# Database
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=healthcare_db
DB_HOST=db
```

### Step 4: Test Your Setup

```bash
python test_backend_auth.py
```

**Success looks like:**
```
✓ Access token obtained (expires in 900s)
✓ Backend Services authentication successful!
✓ Retrieved 5 test patients
✓ ALL TESTS PASSED!
```

**If you see errors:**
- "Private key not found" → Run `python generate_keys.py` again
- "Failed to get access token" → Check your Client ID in `.env`
- "Authentication failed" → Verify public key was uploaded correctly

## 🔒 Key Security Rules

### ✅ DO:
- Keep `private_key.pem` on your computer only
- Add `keys/` folder to `.gitignore` (already done)
- Back up private key to secure location
- Use environment variables for Client ID

### ❌ DON'T:
- Never commit `private_key.pem` to GitHub
- Never share private key with anyone
- Never email or message the private key
- Never upload private key to Epic (only public key!)

## 📋 Quick Reference

| File | What It Is | Where It Goes |
|------|-----------|---------------|
| `keys/private_key.pem` | Your secret key | Stays on YOUR computer |
| `keys/public_key.pem` | Your public key | Upload to Epic's portal |
| Client ID from Epic | Your app identifier | Put in `.env` file |

## 🎯 Visual Flow

```
1. You Generate Keys
   ↓
   keys/private_key.pem (keep secret)
   keys/public_key.pem (share with Epic)

2. Register on Epic Portal
   ↓
   Upload public_key.pem
   ↓
   Epic gives you Client ID

3. Configure Your App
   ↓
   Add Client ID to .env
   ↓
   Point to private_key.pem

4. Your App Uses Both
   ↓
   Private key signs JWTs
   ↓
   Epic verifies with public key
   ↓
   You get access token!
```

## 🆘 Still Stuck?

### Can't find keys after generation?
```bash
ls -la keys/
# Should show:
# private_key.pem
# public_key.pem
```

### Need to view public key contents?
```bash
cat keys/public_key.pem
```

### Epic registration not working?
- Make sure you selected "Backend Services" (not "Standalone")
- Check that you're using Epic's sandbox environment
- Verify your account is verified

### Want to test with a simple curl?
```bash
# This won't work until you register with Epic
curl http://localhost:5000/api/backend/test-connection
```

---

## Next Steps After Setup

Once you have:
- ✅ Keys generated
- ✅ Public key uploaded to Epic
- ✅ Client ID added to .env
- ✅ Test passes

You can:
1. Run your app: `python run.py`
2. Visit: `http://localhost:5000/bulk-backend-export`
3. Click "Export Patients" - NO LOGIN REQUIRED! 🎉

Questions? Let me know what step you're on!
