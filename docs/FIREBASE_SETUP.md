# Firebase Setup Guide for SolveStack

## Overview
We use Firebase Realtime Database for real-time collaboration chat rooms where premium users can discuss and collaborate on problems.

## Setup Steps

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter project name: **SolveStack** (or your preference)
4. Disable Google Analytics (optional for this use case)
5. Click "Create project"

### 2. Enable Realtime Database

1. In your Firebase project, go to **Build** > **Realtime Database**
2. Click "Create Database"
3. Choose a location (closest to your users)
4. Start in **Test mode** (we'll add security rules later)
5. Click "Enable"

### 3. Get Service Account Credentials

1. Go to **Project Settings** (gear icon) > **Service accounts**
2. Click "Generate new private key"
3. Download the JSON file
4. **Important**: Rename it to `firebase-service-account.json`
5. Place it in your project root directory: `d:/major proj demo/`

### 4. Update .env File

Add to your `.env` file:
```bash
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
```

### 5. Add to .gitignore

Make sure `firebase-service-account.json` is in your `.gitignore`:
```
firebase-service-account.json
```

## Security Rules (Production)

Once you're ready for production, update your Firebase Realtime Database rules:

```json
{
  "rules": {
    "collaboration_rooms": {
      "$roomId": {
        ".read": "auth != null",
        ".write": "auth != null"
      }
    }
  }
}
```

## Firebase Web SDK Configuration (Frontend)

For the frontend, you'll also need:

1. Go to **Project Settings** > **General**
2. Scroll to "Your apps" section
3. Click the **Web** icon (`</>`)
4. Register your app
5. Copy the `firebaseConfig` object

This will be used in the React frontend to initialize Firebase.

## Testing Locally

1. Make sure `firebase-service-account.json` is in place
2. Start your backend: `uvicorn main:app --reload`
3. The backend will automatically initialize Firebase Admin SDK
4. Check console output for "Firebase initialized successfully"

## Deployment Notes

**For production deployment (Render, Heroku, etc.):**

Instead of uploading the JSON file:
1. Copy the entire contents of `firebase-service-account.json`
2. Base64 encode it: `cat firebase-service-account.json | base64`
3. Add as environment variable: `FIREBASE_CREDENTIALS_JSON=<base64_string>`
4. Update backend code to read from env variable instead of file

## Troubleshooting

**Error: "Could not find credentials"**
- Check that `firebase-service-account.json` exists in project root
- Verify `FIREBASE_CREDENTIALS_PATH` in `.env` is correct

**Error: "Permission denied"**
- Update Firebase security rules (see above)
- Make sure user is authenticated

**Can't connect to Firebase**
- Check internet connection
- Verify Firebase project is active
- Check Firebase Console for service status
