# Google Drive setup

[PT-BR](../GOOGLE-DRIVE-SETUP.md) | **EN**

This guide explains how to set up Google Drive integration to sync your videos.

## 📋 Prerequisites

- Google Account
- Access to Google Cloud Console
- Backend running (API on port 8000)

## 🔧 Step 1: Create Project on Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select project"** → **"New project"**
3. Project name: `YT-Archiver` (or another name of your choice)
4. Click **"Create"**

## 🔑 Step 2: Activate Google Drive API

1. In the side menu, go to **"APIs and Services"** → **"Library"**
2. Search for **"Google Drive API"**
3. Click on **"Google Drive API"**
4. Click **"Activate"**

## 🎫 Step 3: Create OAuth 2.0 Credentials

### 3.1 Configure Consent Screen

1. Go to **"APIs and Services"** → **"OAuth Consent Screen"**
2. Select **"External"** (unless you have Google Workspace)
3. Click **"Create"**
4. Fill in:
- **App name**: YT-Archiver
- **User support email**: your email
- **App logo**: (optional)
- **Authorized domains**: `localhost` (for development)
- **Developer email**: your email
5. Click **"Save and continue"**

### 3.2 Add Scopes

1. Click **"Add or remove scopes"**
2. Add the scope:
- `https://www.googleapis.com/auth/drive`
- (Required to manage public sharing permissions)
3. Click **"Update"** and then **"Save and Continue"**

### 3.3 Add Test Users

1. Click **"Add users"**
2. Add your Google email
3. Click **"Save and Continue"**

### 3.4 Create Credentials

1. Go to **"APIs and Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth Client ID"**
3. Application Type: **"Desktop Application"**
4. Name: **"YT-Archiver Desktop"**
5. Click **"Create"**

### 3.5 Download Credentials

1. After creating, a popup will appear with your **Client ID** and **Client Secret**
2. Click **"Download JSON"**
3. Save the file as **`credentials.json`**

## 📁 Step 4: Configure in the Project

1. Copy the `credentials.json` file to the `backend/` folder:

```bash
cp ~/Downloads/credentials.json ./backend/credentials.json
```

2. Check if it is in `.gitignore`:

```bash
# The file should already be ignored
cat .gitignore | grep credentials.json
```

## 🚀 Step 5: Authenticate in the Web Interface

1. Launch the backend:

```bash
cd backend
./run.sh
```

2. Start the frontend (in another terminal):

```bash
cd frontend
npm run dev
```

3. Access http://localhost:3000/drive

4. Click **"Connect with Google Drive"**

5. Authorize the application on the Google screen:
- Choose your account
- Click **"Allow"** to give access to Drive

6. After authorizing, you will be redirected back and see your videos!

### First use of the catalog (recommended)

- **New machine (snapshot already exists in Drive):**
- `POST /api/catalog/drive/import`
- **Drive already populated, without snapshot:**
- `POST /api/catalog/drive/rebuild`
- **Index existing local videos:**
- `POST /api/catalog/bootstrap-local`

## 🔐 Security

### Sensitive Files (DO NOT commit)

These files contain sensitive information and should **NOT** be committed to Git:

- `backend/credentials.json` - OAuth credentials
- `backend/token.json` - Access token generated after authentication
- `backend/uploaded.jsonl` - Upload log

Everyone is already on `.gitignore`.

### Credential Rotation

If you accidentally expose your credentials:

1. Go to the Google Cloud Console
2. **"APIs and Services"** → **"Credentials"**
3. Click the trash can next to the compromised credentials
4. Create new credentials by following Step 3 again

## 📊 Structure in Drive

After authenticating, the system will automatically create:

```
Google Drive/
└── YouTube Archiver/           # Pasta raiz
    ├── Canal A/
    │   ├── Video 1.mp4
    │   └── Video 2.mp4
    └── Canal B/
        └── Playlist/
            └── Video 3.mp4
```

The local folder structure will be mirrored in Drive.

## ❓ Troubleshooting

### Error: "Credentials file not found"

**Workaround:** Make sure `credentials.json` is in `backend/credentials.json`.

### Error: "redirect_uri_mismatch"

**Cause:** The redirect URI is not configured in Google Cloud.

**Solution:**
1. Go to **"Credentials"** in the Google Cloud Console
2. Edit your OAuth Client ID
3. Under **"Authorized redirect URIs"**, add:
- `http://localhost:8000/api/drive/oauth2callback`
4. Save

### Error: "Access blocked: Authorization Error"

**Cause:** App is in test mode and you are not an authorized user.

**Solution:**
1. Go to **"OAuth Consent Screen"**
2. Under **"Test Users"**, add your email
3. Or, publish the app (not recommended for personal use)

### Expired token

The token expires after some time. The system will automatically renew the token using `refresh_token`. If this fails:

1. Delete `backend/token.json`
2. Re-authenticate to `/drive`

### Error: "Scope has changed"

**Cause:** The old token was generated with a different scope.

**Solution:**
1. Delete `backend/token.json`
2. Restart the backend
3. Re-authenticate to `/drive`

## 🎯 Next Steps

After configuring:

1. ✅ Access `/drive` on the web interface
2. ✅ See sync status (Local vs Drive)
3. ✅ Upload individual or batch videos
4. ✅ Manage your videos in Drive

## 📚 Additional Resources

- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [YT-Archiver README](../../../README.en.md)
