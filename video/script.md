# Sell Smart — farmer onboarding video

Outputs: `web/video/onboarding_{mr,hi,en}.mp4` (served at `/app/video/onboarding_<lang>.mp4`), 1080x1920, ~59 s each.

## Re-render
```
python3 video/tts.py mr hi en     # Sarvam bulbul:v3 'shubh'; skips audio/ files that exist (delete one to redo it)
PW=<path to node_modules/playwright> node video/record.js mr   # also hi, en
```
`scene.html` is a fake Telegram chat driven frame-by-frame (`setup(lang, durations)` + `seek(t)`); open `scene.html?lang=mr` in a browser for a live preview.
Each step lasts max(minimum animation time, narration length + 1.6 s); narration starts 0.3 s into the step.

## Steps (re-record with a real phone in this order)
1. Open Telegram → search **@SellSmartKisanBot** → tap **START**
2. Bot greets and asks NAME, with language buttons मराठी / हिंदी / English → farmer taps language, types name (रामेश)
3. Bot: "धन्यवाद रामेश! 📍 तुमचे ठिकाण पाठवा, किंवा ६ अंकी पिनकोड लिहा" → tap **📍 माझे ठिकाण पाठवा** → location bubble (Niphad, Nashik)
4. Bot: "🌾 कोणते पीक विकायचे?" → buttons कांदा, टोमॅटो, सोयाबीन, गहू, हरभरा, तूर, बटाटा, डाळिंब, मका, कापूस, इतर → tap कांदा
5. Bot: "⚖️ किती क्विंटल?" → buttons 10, 20, 50, 100, 200, ✍️ लिहा → tap 50
6. Advice card: map pin + लासलगाव बाजार, नाशिक · १८ किमी · आज; ₹4,300 × 50 = ₹2,15,000 − ट्रक भाडे ₹25/किमी (₹450) − हमाली ₹1,000 = 💰 हातात ₹2,13,550; ₹16,000 more than nearest market; खात्री: मध्यम. Buttons 🛒 थेट विक्री | 🤝 ट्रक शेअर | 📸 साठवण फोटो | 🔁 नवीन सल्ला
7. Tips: 🎙️ ask by voice note; 📸 send a photo of stored crop → shelf-life estimate
8. End card: "निर्णय तुमचा. माहिती आमची. 🙏" + @SellSmartKisanBot

## Narration — Marathi (506 chars)
1. टेलिग्राम उघडा. सेल स्मार्ट किसान बॉट शोधा, आणि स्टार्ट दाबा.
2. बॉट तुमचे नाव विचारेल. भाषा निवडा, आणि तुमचे नाव लिहून पाठवा.
3. माझे ठिकाण पाठवा, हे बटण दाबा. किंवा सहा अंकी पिनकोड लिहा.
4. कोणते पीक विकायचे आहे, त्याचे बटण दाबा. जसे, कांदा.
5. आता, किती क्विंटल माल आहे, ते निवडा.
6. बॉट सांगेल, कोणत्या बाजारात विकल्यावर, ट्रक भाडे आणि हमाली वजा करून, तुमच्या हातात सर्वात जास्त पैसे येतील.
7. तुम्ही बोलूनही विचारू शकता. साठवलेल्या मालाचा फोटो पाठवा, तो किती दिवस टिकेल ते आम्ही सांगू.
8. निर्णय तुमचा. माहिती आमची. आजच सुरू करा!

## Narration — Hindi (495 chars)
1. टेलीग्राम खोलिए. सेल स्मार्ट किसान बॉट खोजिए, और स्टार्ट दबाइए.
2. बॉट आपका नाम पूछेगा. भाषा चुनिए, और अपना नाम लिखकर भेजिए.
3. मेरा स्थान भेजें, यह बटन दबाइए. या छह अंकों का पिनकोड लिखिए.
4. कौन सी फसल बेचनी है, उसका बटन दबाइए. जैसे, प्याज़.
5. अब, कितने क्विंटल माल है, वह चुनिए.
6. बॉट बताएगा कि किस मंडी में बेचने पर, ट्रक भाड़ा और हमाली काटकर, आपके हाथ में सबसे ज़्यादा पैसा आएगा.
7. आप बोलकर भी पूछ सकते हैं. रखे हुए माल की फोटो भेजिए, वह कितने दिन टिकेगा, हम बताएँगे.
8. फ़ैसला आपका. जानकारी हमारी. आज ही शुरू कीजिए!

## Narration — English (540 chars)
1. Open Telegram. Search for Sell Smart Kisan Bot, and tap Start.
2. The bot will ask your name. Choose your language, and type your name.
3. Tap the button, send my location. Or type your six digit pincode.
4. Tap the crop you want to sell. For example, onion.
5. Now choose how many quintals you have.
6. The bot tells you which market gives the most money in your hand, after truck rent and loading charges.
7. You can also ask by voice. Send a photo of your stored crop, and we will tell you how many days it will last.
8. Your decision. Our information. Start today!
