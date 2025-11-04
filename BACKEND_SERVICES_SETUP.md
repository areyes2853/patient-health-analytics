# Backend Services Setup Guide

## 🎯 Problem Solved
**No more MyChart login required for bulk operations!**

Your app was experiencing login issues because it was using **Standalone OAuth** (user login flow). Backend Services provides **system-to-system authentication** that never requires user login - perfect for automated bulk data operations.

## 📋 Prerequisites

1. **Epic FHIR Sandbox Account**
   - Sign up at https://fhir.epic.com/
   - You'll need to register for Backend Services access

2. **Python 3.8+** with pip
3. **PostgreSQL** (via Docker or local)

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
cd /Users/angelminimac/Desktop/GA-project/code/ga/labs/-intro-to-mongoose-lab-/patient-health-analytics

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Generate RSA Keys

```bash
python generate_keys.py
```

This will create:
- `keys/private_key.pem` - **Keep this SECRET!**
- `keys/public_key.pem` - You'll register this with Epic

**Important:** Never commit private keys to git (already in .gitignore)

### Step 3: Register with Epic

1. Go to Epic's FHIR sandbox: https://fhir.epic.com/
2. Navigate to **Backend Services** registration
3. Upload your `public_key.pem` file
4. You'll receive a **Client ID** for backend services

### Step 4: Configure Environment

Copy and edit your `.env` file:

```bash
cp .env.example .env
```

Update these values in `.env`:

```env
# Backend Services Configuration
EPIC_BACKEND_CLIENT_ID=your-backend-client-id-here
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
EPIC_FHIR_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
PRIVATE_KEY_PATH=./keys/private_key.pem
```

### Step 5: Test Connection

```bash
python test_backend_auth.py
```

Expected output:
```
✓ Access token obtained
✓ Backend Services authentication successful!
✓ Retrieved 5 test patients
✓ ALL TESTS PASSED!
```

### Step 6: Run the App

```bash
# Option 1: Direct Python
python run.py

# Option 2: Docker
docker-compose up
```

Visit: `http://localhost:5000/bulk-backend-export`

## 🔑 Key Differences

### Old Way (Standalone OAuth)
- ❌ Requires user to log into MyChart
- ❌ Session expires
- ❌ Can break with login issues
- ✅ Good for patient-facing apps

### New Way (Backend Services)
- ✅ No user login required
- ✅ System-to-system authentication
- ✅ Always available
- ✅ Perfect for bulk operations

## 🎨 Available Endpoints

### Backend Services Routes

```
GET  /api/backend/test-connection
     Test if backend auth is working

GET  /api/backend/bulk-patients?count=100
     Export patients without user login

GET  /api/backend/patient/{id}/observations
     Get patient observations

POST /api/backend/bulk-export-start
     Initiate full FHIR bulk export

POST /api/backend/bulk-export-status
     Check bulk export status
```

### UI Pages

```
/bulk-backend-export  - New automated bulk export page (no login!)
/bulk-epic-export     - Old page (requires user login)
/epic-dashboard       - Original dashboard (requires user login)
```

## 🧪 Testing

### Quick Test
```bash
# Test connection
curl http://localhost:5000/api/backend/test-connection

# Export 10 patients
curl http://localhost:5000/api/backend/bulk-patients?count=10
```

### Full Test in Browser
1. Go to `http://localhost:5000/bulk-backend-export`
2. Click "Test Backend Connection"
3. Set patient count and click "Export Patients"
4. No login required! 🎉

## 🔒 Security Notes

1. **Private Key Protection**
   - Never commit `private_key.pem` to version control
   - Store securely in production (e.g., AWS Secrets Manager)
   - Already added to `.gitignore`

2. **Token Management**
   - Access tokens cached and auto-refreshed
   - Expire after 15 minutes (automatically renewed)
   - No manual token management needed

3. **Scope Permissions**
   - Currently set to: `system/Patient.read system/Observation.read`
   - Adjust scopes in `epic_backend_auth.py` as needed

## 📊 Example Usage in Code

```python
from epic_backend_auth import EpicBackendAuth, EpicBulkExport

# Initialize (no user interaction needed)
auth = EpicBackendAuth()
bulk = EpicBulkExport(auth)

# Export 100 patients - completely automated!
patients = bulk.simple_patient_export(count=100)

# Process data
for patient in patients:
    print(f"Patient: {patient['id']}")
```

## 🐛 Troubleshooting

### "Private key not found"
```bash
python generate_keys.py
```

### "Failed to get access token"
- Check `EPIC_BACKEND_CLIENT_ID` in `.env`
- Verify public key is registered with Epic
- Check `EPIC_TOKEN_URL` is correct

### "Authentication failed"
- Ensure you registered for **Backend Services** (not just Standalone OAuth)
- Verify client ID matches the one Epic provided
- Check that public key was uploaded correctly

### "Module not found"
```bash
pip install -r requirements.txt
```

## 🎯 Production Deployment

1. **Environment Variables**
   - Use environment-specific configs
   - Never hardcode credentials

2. **Key Management**
   - Use secure secret storage (AWS Secrets Manager, Azure Key Vault)
   - Rotate keys periodically

3. **Monitoring**
   - Log authentication attempts
   - Monitor token refresh failures
   - Set up alerts for auth errors

## 📚 Additional Resources

- [Epic Backend Services Documentation](https://fhir.epic.com/Documentation?docId=oauth2&section=BackendOAuth2Guide)
- [FHIR Bulk Data Specification](http://hl7.org/fhir/uv/bulkdata/)
- [SMART Backend Services](http://hl7.org/fhir/smart-app-launch/backend-services.html)

## 🆘 Support

If you run into issues:
1. Check Epic's sandbox status page
2. Review error messages in console
3. Run `python test_backend_auth.py` for diagnostics
4. Check that all dependencies are installed

## ✅ Success Checklist

- [ ] Generated RSA keys
- [ ] Registered public key with Epic
- [ ] Updated `.env` with backend client ID
- [ ] Tested connection with `test_backend_auth.py`
- [ ] Can access `/bulk-backend-export` page
- [ ] Successfully exported patients without login
- [ ] Confirmed keys are in `.gitignore`

---

**Your app is now ready for automated bulk operations! 🎉**
