# Quick Testing Guide for SolveStack

## 🚀 How to Start Everything

### Step 1: Start Backend (Already Running! ✅)
Your backend is already running at `http://localhost:8000`

If you need to restart it:
```bash
# Activate venv
d:/major proj demo/venv/Scripts/Activate.ps1

# Start backend
uvicorn main:app --reload
```

### Step 2: Start Frontend

In a **new terminal**:
```bash
cd "d:/major proj demo/problem-shelf-frontend"
npm start
```

This will open `http://localhost:3000` in your browser automatically.

---

## ✅ Step-by-Step Testing Flow

### Test 1: Register a New User

1. Open `http://localhost:3000`
2. Click **"Register"** button in navbar
3. Fill in:
   - Email: `test@example.com`
   - Username: `testuser`
   - Password: `password123`
   - Confirm Password: `password123`
4. Click **"Register"**
5. ✅ Should auto-login and redirect to dashboard
6. ✅ See username with profile icon in navbar

### Test 2: Explore Problems

1. You should see problems on the dashboard
2. If no problems:
   - Click **"Admin"** in navbar
   - Click **"Trigger Scraping"** to fetch problems from Reddit/GitHub
   - Wait ~30 seconds
   - Go back to dashboard

### Test 3: Mark Interest in Problems

1. Find a problem card
2. Click the **heart icon** (top right of card)
3. ✅ Heart should fill with red color
4. ✅ Interest count should increase
5. Click heart again
6. ✅ Heart becomes outline
7. ✅ Count decreases

### Test 4: View Profile

1. Click **profile icon** (top right navbar)
2. Select **"Profile"**
3. ✅ See your username and email
4. ✅ See all problems you marked interest in

### Test 5: Logout and Login

1. Click profile icon → **"Logout"**
2. Click **"Login"**
3. Enter:
   - Email: `test@example.com`
   - Password: `password123`
4. Click **"Login"**
5. ✅ Should be logged in again
6. ✅ Your interests should still be there

### Test 6: Protected Routes

1. Logout
2. Try to visit `http://localhost:3000/profile` directly
3. ✅ Should redirect to login page
4. Login → should access profile

---

## 🐛 Common Issues

**"This site can't be reached" on localhost:3000**
- Make sure frontend is running: `npm start` in problem-shelf-frontend folder
- Check for errors in terminal

**"Cannot connect to backend"**
- Make sure backend is running: `uvicorn main:app --reload`
- Check it's on port 8000: visit `http://localhost:8000` (should see "healthy")

**No problems showing**
- Go to Admin panel
- Click "Trigger Scraping"
- Wait for completion
- Refresh dashboard

**Can't mark interest**
- Make sure you're logged in
- Check browser console (F12) for errors

---

## 📱 What to Look For

### ✅ Authentication Working:
- Register creates account
- Login works
- Logout clears session
- Protected routes redirect to login

### ✅ Interest Tracking Working:
- Heart icon toggles
- Count updates in real-time
- Profile shows interests
- State persists after refresh

### ✅ UI Working:
- Navbar shows login/logout buttons correctly
- Loading spinners appear when fetching data
- Premium chip shows if user is premium
- Responsive grid layout on different screen sizes

---

## 🎯 Quick Commands Summary

```bash
# Backend (Terminal 1)
cd "d:/major proj demo"
uvicorn main:app --reload

# Frontend (Terminal 2) 
cd "d:/major proj demo/problem-shelf-frontend"
npm start
```

---

## 💡 Tips

- **Use Chrome DevTools** (F12) to see network requests and console logs
- **Try multiple users** - register 2-3 users to see interest counts increase
- **Test on mobile view** - resize browser to see responsive design
- **Check backend logs** - see API calls in the uvicorn terminal

---

**Need help?** Check the full walkthrough in the artifacts for detailed explanations!
