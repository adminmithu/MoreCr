# 🚀 Render.com এ ডিপ্লয় করার সম্পূর্ণ গাইড (Render Deployment Guide)

এই বট এবং ওয়েব ড্যাশবোর্ডটি **Render.com** এর ফ্রি টিয়ারে (Free Web Service) ২৪/৭ চালানোর জন্য প্রস্তুত করা হয়েছে।

---

## 📋 ডিপ্লয়মেন্ট সেটিংস একনজরে (Settings Overview)

| অপশন | মান (Value) |
|---|---|
| **Service Type** | **Web Service** |
| **Environment / Runtime** | **Python** |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python main.py` |
| **Plan** | **Free** |
| **Health Check Path** | `/` |

---

## 🛠️ ধাপে ধাপে ডিপ্লয় করার নিয়ম (Step-by-Step Instructions)

### ধাপ ১: GitHub এ কোড আপলোড করুন
1. [GitHub.com](https://github.com/) এ লগইন করে একটি নতুন Repository তৈরি করুন (যেমন: `MoreLoginCreator`).
2. `d:\MoreLoginCreator\` ফোল্ডারের ফাইলগুলো আপনার রিপোজিটরিতে আপলোড/পুশ করুন।

---

### ধাপ ২: Render.com এ Web Service তৈরি করুন
1. [Render.com](https://dashboard.render.com/) এ লগইন করুন।
2. **`New +`** বাটনে ক্লিক করে **`Web Service`** সিলেক্ট করুন।
3. আপনার GitHub রিপোজিটরিটি সিলেক্ট করে **`Connect`** বাটনে চাপ দিন।

---

### ধাপ ৩: কনফিগারেশন পূরণ করুন
Render এর ফর্মে নিচের তথ্যগুলো পূরণ করুন:

- **Name:** `morelogin-bot` (বা আপনার পছন্দের নাম)
- **Region:** `Oregon (US West)` বা যেকোনোটি
- **Branch:** `main` (বা master)
- **Runtime:** `Python 3`
- **Build Command:** 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command:** 
  ```bash
  python main.py
  ```

---

### ধাপ ৪: Environment Variables (এনভায়রনমেন্ট ভেরিয়েবলস) সেট করুন
নিচে স্ক্রল করে **Environment Variables** সেকশনে যান এবং **`Add Environment Variable`** এ ক্লিক করে নিচের ভেরিয়েবলগুলো যোগ করুন:

| Key | Value |
|---|---|
| `BOT_TOKEN` | `9102184863:AAEA4W0Q0PjNC3fV04g3ii6vEULEIWYjKM0` |
| `ADMIN_IDS` | `8929349073` |
| `ENABLE_WEB_DASHBOARD` | `true` |
| `DEFAULT_EMAIL_PREFIX` | `priyaahmed210208` |
| `DEFAULT_PASSWORD` | `MoreLogin@2026!` |
| `REALTIME_ADMIN_PUSH` | `true` |
| `PYTHON_VERSION` | `3.11.9` |

*(নোট: `PORT` ভেরিয়েবল Render নিজে থেকেই প্রদান করে, যা আমাদের `config.py` অটোমেটিক ডিটেক্ট করে নেবে)*

---

### ধাপ ৫: Deploy বাটনে চাপ দিন
- নিচে থাকা **`Create Web Service`** বাটনে চাপ দিন।
- Render ডিপ্লয়মেন্ট শুরু করবে এবং `pip install` শেষ করে বটটি চালু করবে।
- ডিপ্লয় সম্পন্ন হলে আপনি একটি লাইভ URL পাবেন, যেমন:
  👉 **`https://morelogin-bot.onrender.com`**
- এই লিঙ্কে ঢুকলে সরাসরি আপনার **Windows Live Browser Automation Window** এবং **কন্ট্রোল ড্যাশবোর্ড** দেখতে পাবেন!
- একই সাথে টেলিগ্রামের [@moreloginsellerbot](https://t.me/moreloginsellerbot) ২৪/৭ লাইভ চলবে!

---

## 💡 বোনাস টিপ: ফ্রি টিয়ারকে ২৪/৭ সচল রাখা (Keep Awake)
Render এর ফ্রি ওয়েব সার্ভিস ১৫ মিনিট ইনএকটিভ থাকলে স্লিপ মোডে যেতে পারে। এটিকে সারাক্ষণ ১০০% অ্যাক্টিভ রাখতে:
1. [UptimeRobot.com](https://uptimerobot.com/) বা [cron-job.org](https://cron-job.org/) এ ফ্রি একাউন্ট খুলুন।
2. **Add New Monitor** এ ক্লিক করে আপনার Render URL (যেমন: `https://morelogin-bot.onrender.com`) দিন।
3. Interval দিন **`10 minutes`**।
4. ব্যস! আপনার বট ও ওয়েব ড্যাশবোর্ড কখনো স্লিপে যাবে না, সারাক্ষণ নিরবচ্ছিন্ন চলবে।
