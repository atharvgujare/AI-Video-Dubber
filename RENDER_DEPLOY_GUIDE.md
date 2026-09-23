# 🚀 Render.com 100% Free Cloud Deployment Guide

This guide walks you through deploying **AI Dubber Studio** to **Render.com** at **$0.00 cost** (no credit card required).

Once deployed:
- ✅ Your laptop can be completely turned **OFF**.
- ✅ Works on **any network** (mobile 5G/4G, work Wi-Fi, anywhere).
- ✅ Has a permanent **HTTPS (SSL)** address.
- ✅ Installs directly on your **mobile phone** as a standalone app!
- ✅ Updates automatically whenever you push code changes.

---

## 📋 Prerequisites (All 100% Free)
1. A **GitHub account** ([github.com](https://github.com/join))
2. A **Render.com account** ([render.com](https://render.com) — click *Sign in with GitHub*)
3. *(Optional for ~2s transcription)*: A free **Groq Cloud API Key** ([console.groq.com/keys](https://console.groq.com/keys))

---

## 🛠️ Step 1: Push Code to GitHub

If you already have Git installed or use GitHub Desktop:

### Option A: Using Command Line / Terminal
In your project directory (`d:\youtube_ai_dubber\youtube_ai_dubber`):

```bash
git init
git add .
git commit -m "Deploy AI Dubber Studio v2.2.0 Cloud Edition"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/youtube-ai-dubber.git
git push -u origin main
```
*(Replace `YOUR_USERNAME/youtube-ai-dubber` with your repository URL).*

### Option B: Using GitHub Desktop
1. Open **GitHub Desktop** > File > **Add Local Repository**.
2. Select `d:\youtube_ai_dubber\youtube_ai_dubber`.
3. Click **Publish Repository** to GitHub (keep it Public or Private).

---

## ☁️ Step 2: Deploy to Render.com

1. Go to [dashboard.render.com](https://dashboard.render.com) and log in.
2. Click the **"New +"** button at the top and select **"Web Service"**.
3. Choose **"Build and deploy from a Git repository"** and click **Next**.
4. Select your **`youtube-ai-dubber`** repository.
5. Render will automatically detect our `render.yaml` blueprint! If setting manually, enter:
   - **Name**: `ai-dubber-studio`
   - **Runtime**: `Python`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `python -m uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free ($0/month)**
6. *(Optional)* In **Environment Variables**, add:
   - `GROQ_API_KEY`: *(paste your free Groq API key from console.groq.com for ~2s transcription)*
7. Click **"Create Web Service"**.

Render will now:
- Install Python packages.
- Compile the React frontend into `dist/`.
- Deploy your server in ~2 minutes.

When the deploy finishes, you will see a green **"Live"** badge and your permanent URL:
👉 **`https://ai-dubber-studio.onrender.com`**

---

## 📱 Step 3: Install App on Your Smartphone

1. On your phone (Android or iPhone), open **Chrome** or **Safari**.
2. Go to your new Render link: `https://your-app-name.onrender.com`.
3. You will see the secure padlock icon 🔒 in the address bar.
4. **Android (Chrome)**:
   - Tap the **three dots menu (⋮)** > Tap **"Install app"**.
5. **iPhone (Safari)**:
   - Tap the **Share icon [↑]** > Tap **"Add to Home Screen"**.
6. The app is now installed on your phone! Tap the icon on your home screen to launch AI Dubber Studio in full screen without any browser bars.

---

## 🔄 How Future Updates Work

Updating the app is completely automated:

1. Whenever new features are pushed to GitHub (`git push`):
   - Render automatically detects the commit.
   - Render rebuilds and redeploys the cloud server in the background.
2. The next time you open the app on your phone, you will see an in-app banner:
   > **"✨ New Studio Update Available! [Tap to Update]"**
3. Tap **"Update Now"**, and the new version loads immediately onto your phone!
