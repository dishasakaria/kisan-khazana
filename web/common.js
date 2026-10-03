// Shared by all pages: i18n (mr default / hi / en), API fetch with mock fallback, ₹ formatting.
const STR = {
  nav_home: ["मुख्यपृष्ठ", "होम", "Home"],
  nav_fpo: ["FPO डॅशबोर्ड", "FPO डैशबोर्ड", "FPO dashboard"],
  nav_buy: ["थेट खरेदी", "सीधे खरीदें", "Buy direct"],
  demo: ["डेमो डेटा", "डेमो डेटा", "demo data"],
  // landing
  hero_title: ["शेतमाल कुठे आणि कधी विकायचा — आता अंदाज नाही, आकडे.", "फसल कहाँ और कब बेचें — अब अंदाज़ा नहीं, आंकड़े।", "Where and when to sell your crop — numbers, not guesswork."],
  hero_sub: ["सेल-स्मार्ट पुढील ३ आठवड्यांचे मंडी भाव, वाहतूक खर्च आणि धोका मोजून शेतकऱ्याला हातात जास्तीत जास्त पैसा मिळेल असा सल्ला देते.", "सेल-स्मार्ट अगले 3 हफ़्तों के मंडी भाव, ढुलाई ख़र्च और जोखिम जोड़कर किसान को सबसे ज़्यादा हाथ में आने वाले पैसे की सलाह देता है।", "Sell Smart forecasts mandi prices for the next 3 weeks, nets out transport and risk, and tells farmers the option that puts the most money in hand."],
  c1_t: ["शेतकरी — टेलिग्रामवर", "किसान — टेलीग्राम पर", "Farmers — on Telegram"],
  c1_d: ["\"कांदा 50 क्विंटल\" असे लिहा किंवा बोला. कोणती मंडी, कधी, किती पैसे — मराठीत उत्तर.", "\"प्याज 50 क्विंटल\" लिखें या बोलें। कौन सी मंडी, कब, कितना पैसा — अपनी भाषा में जवाब।", "Type or say \"onion 50 quintal\". Get which mandi, when, and how much — in your language."],
  c1_a: ["टेलिग्राम बॉट उघडा", "टेलीग्राम बॉट खोलें", "Open Telegram bot"],
  c2_t: ["FPO डॅशबोर्ड", "FPO डैशबोर्ड", "FPO dashboard"],
  c2_d: ["3D नकाशावर मंडी भावाचा अंदाज, सदस्यांचा साठा, एकत्र वाहतूक (कारपूल) आणि आमच्या अंदाजांची अचूकता.", "3D नक्शे पर मंडी भाव का अनुमान, सदस्यों का स्टॉक, साझा ढुलाई (कारपूल) और हमारे अनुमानों की सटीकता।", "3D map of forecast mandi prices, member stock, shared transport (carpools) and our forecast track record."],
  c2_a: ["डॅशबोर्ड उघडा", "डैशबोर्ड खोलें", "Open dashboard"],
  c3_t: ["थेट शेतकऱ्याकडून खरेदी", "सीधे किसान से खरीदें", "Buy direct from farmers"],
  c3_d: ["व्यापारी, प्रक्रिया उद्योग, निर्यातदार आणि FPO खरेदी: जवळचा माल, आजचा योग्य भाव, थेट ऑफर. शुल्क फक्त 1%.", "व्यापारी, प्रोसेसर, निर्यातक और FPO ख़रीद: पास का माल, आज का सही भाव, सीधा ऑफ़र। शुल्क सिर्फ़ 1%।", "Traders, processors, exporters and FPO procurement: produce nearby, today's fair price, direct offers. Just 1% fee."],
  c3_a: ["खरेदी सुरू करा", "ख़रीदारी शुरू करें", "Start buying"],
  track_title: ["आमचा रेकॉर्ड", "हमारा रिकॉर्ड", "Track record"],
  track_err: ["सरासरी अंदाज चूक", "औसत अनुमान त्रुटि", "Average forecast error"],
  track_in: ["खरा भाव अंदाज-पट्ट्यात", "असली भाव अनुमान-दायरे में", "Real price inside our range"],
  track_n: ["तपासलेले अंदाज", "जाँचे गए अनुमान", "Forecasts checked"],
  track_crops: ["पिके", "फसलें", "Crops covered"],
  pilot: ["पायलट: पुणे, नाशिक, अहिल्यानगर जिल्हे, महाराष्ट्र", "पायलट: पुणे, नासिक, अहिल्यानगर ज़िले, महाराष्ट्र", "Pilot: Pune, Nashik, Ahilyanagar districts, Maharashtra"],
  // landing v2
  tg_start: ["Telegram वर सुरू करा", "Telegram पर शुरू करें", "Start on Telegram"],
  call: ["कॉल करा", "कॉल करें", "Call us"],
  sms: ["स्मार्टफोन नाही? साधा कॉल किंवा SMS ही चालतो.", "स्मार्टफ़ोन नहीं? सामान्य कॉल या SMS भी चलेगा।", "No smartphone? A plain call or SMS works too."],
  free: ["शेतकऱ्यांसाठी मोफत सल्ला · मराठी, हिंदी, English", "किसानों के लिए मुफ़्त सलाह · मराठी, हिंदी, English", "Free advice for farmers · Marathi, Hindi, English"],
  sample: ["नमुना सल्ला", "नमूना सलाह", "Sample advice"],
  adv_q: ["कांदा 50 क्विंटल", "प्याज 50 क्विंटल", "Onion 50 quintal"],
  adv_title: ["आजचा सल्ला", "आज की सलाह", "Today's advice"],
  adv_verdict: ["आता विका — लासलगाव मंडी", "अभी बेचें — लासलगाव मंडी", "Sell now — Lasalgaon mandi"],
  adv_price: ["अपेक्षित भाव", "अपेक्षित भाव", "Expected price"],
  adv_truck: ["ट्रक भाडे", "ट्रक भाड़ा", "Truck cost"],
  adv_hand: ["तुमच्या हातात", "आपके हाथ में", "Money in hand"],
  adv_wait: ["14 दिवस थांबल्यास (अंदाज)", "14 दिन रुकने पर (अनुमान)", "If you wait 14 days (forecast)"],
  adv_note: ["थांबून फायदा कमी, कांदा खराब होण्याचा धोका जास्त. निर्णय तुमचा.", "रुकने में फ़ायदा कम, प्याज़ ख़राब होने का जोखिम ज़्यादा। फ़ैसला आपका।", "Little upside in waiting, real spoilage risk. Your call."],
  how_title: ["कसे चालते? फक्त 3 गोष्टी सांगा", "कैसे चलता है? बस 3 बातें बताएं", "How it works: tell us 3 things"],
  st1_t: ["नाव", "नाम", "Name"],
  st1_d: ["तुमचे नाव सांगा", "अपना नाम बताएं", "Tell us your name"],
  st2_t: ["ठिकाण", "स्थान", "Location"],
  st2_d: ["गाव, पिनकोड किंवा लोकेशन पाठवा", "गाँव, पिनकोड या लोकेशन भेजें", "Village, pincode or share location"],
  st3_t: ["पीक आणि क्विंटल", "फसल और क्विंटल", "Crop & quintals"],
  st3_d: ["\"कांदा 50 क्विंटल\" — लिहा किंवा बोला", "\"प्याज 50 क्विंटल\" — लिखें या बोलें", "\"onion 50 quintal\" — type or speak"],
  st4_t: ["सल्ला", "सलाह", "Advice"],
  st4_d: ["कोणती मंडी, कधी, हातात किती — लगेच", "कौन सी मंडी, कब, हाथ में कितना — तुरंत", "Which mandi, when, money in hand — instantly"],
  vid_title: ["1 मिनिटात पहा", "1 मिनट में देखें", "See it in 1 minute"],
  f_title: ["सेल-स्मार्ट तुमच्यासाठी काय करते", "सेल-स्मार्ट आपके लिए क्या करता है", "What Sell Smart does for you"],
  f1_t: ["सर्वोत्तम मंडी, ट्रक खर्च वजा करून", "सबसे अच्छी मंडी, ट्रक ख़र्च घटाकर", "Best mandi, after truck cost"],
  f1_d: ["जवळच्या मंडींचे भाव, अंतर आणि ट्रक भाडे मोजून — हातात सर्वाधिक पैसा कुठे ते सांगतो.", "पास की मंडियों के भाव, दूरी और ट्रक भाड़ा जोड़कर — हाथ में सबसे ज़्यादा पैसा कहाँ, यह बताता है।", "Compares nearby mandi prices, distance and truck fare — tells you where you keep the most money."],
  f2_t: ["आता विकू की थांबू?", "अभी बेचूँ या रुकूँ?", "Sell now or wait?"],
  f2_d: ["पुढील 3 आठवड्यांचा भाव अंदाज आणि साठवणुकीतील नुकसान धरून स्पष्ट उत्तर.", "अगले 3 हफ़्तों का भाव अनुमान और भंडारण नुकसान जोड़कर साफ़ जवाब।", "3-week price forecast plus storage losses, turned into a clear answer."],
  f3_t: ["नासाडी घड्याळ 📷", "ख़राबी घड़ी 📷", "Spoilage Clock 📷"],
  f3_d: ["साठवलेल्या मालाचा फोटो पाठवा — दर्जा, अंदाजे प्रमाण आणि रोज किती खराब होतोय ते कळते.", "भंडारित माल की फ़ोटो भेजें — हालत, अनुमानित मात्रा और रोज़ कितना ख़राब हो रहा है, पता चलेगा।", "Send a photo of stored produce — get its condition, rough quantity and daily spoilage rate."],
  f4_t: ["ट्रक शेअरिंग", "ट्रक शेयरिंग", "Truck sharing"],
  f4_d: ["एकाच मंडीला जाणारे जवळचे शेतकरी एका ट्रकमध्ये — भाडे विभागून बचत.", "एक ही मंडी जाने वाले पास के किसान एक ट्रक में — भाड़ा बाँटकर बचत।", "Nearby farmers heading to the same mandi share one truck and split the fare."],
  f5_t: ["थेट घाऊक खरेदीदार", "सीधे थोक ख़रीदार", "Direct wholesale buyers"],
  f5_d: ["व्यापारी, प्रक्रिया उद्योग, निर्यातदार थेट ऑफर देतात. शुल्क फक्त 1% (अडत 6–8%).", "व्यापारी, प्रोसेसर, निर्यातक सीधे ऑफ़र देते हैं। शुल्क सिर्फ़ 1% (आढ़त 6–8%)।", "Traders, processors and exporters make direct offers. Just 1% fee (vs 6–8% commission)."],
  trust_title: ["विश्वास — आम्ही आकडे लपवत नाही", "भरोसा — हम आंकड़े नहीं छिपाते", "Trust — we show our numbers"],
  bt_t: ["2025 चाचणी: अंदाजातील चूक", "2025 परीक्षण: अनुमान में त्रुटि", "2025 test: forecast error"],
  bt_ours: ["सेल-स्मार्ट अंदाज", "सेल-स्मार्ट अनुमान", "Sell Smart forecast"],
  bt_naive: ["\"भाव तसाच राहील\"", "\"भाव वैसा ही रहेगा\"", "\"Price stays same\""],
  bt_note: ["2025 च्या खऱ्या मंडी भावांवर तपासले (मॉडेलने आधी न पाहिलेला डेटा). कमी चूक = चांगले.", "2025 के असली मंडी भावों पर जाँचा (मॉडल ने पहले न देखा डेटा)। कम त्रुटि = बेहतर।", "Checked against real 2025 mandi prices the model never saw. Lower error = better."],
  u_t: ["एक आकडा नाही — पट्टा", "एक आंकड़ा नहीं — दायरा", "A range, not a single number"],
  u_d: ["प्रत्येक अंदाजासोबत शक्य पट्टा (उदा. ₹1,650–₹2,050). खात्री कमी असेल तर तसे स्पष्ट सांगतो.", "हर अनुमान के साथ संभावित दायरा (जैसे ₹1,650–₹2,050)। भरोसा कम हो तो साफ़ बताते हैं।", "Every forecast comes with a likely range (e.g. ₹1,650–₹2,050). When we're unsure, we say so."],
  d_t: ["निर्णय तुमचा", "फ़ैसला आपका", "Your decision"],
  d_d: ["आम्ही आकडे आणि धोका दाखवतो. विकायचे की थांबायचे — ते तुम्हीच ठरवा.", "हम आंकड़े और जोखिम दिखाते हैं। बेचना है या रुकना — आप तय करें।", "We show the numbers and the risk. Whether to sell or wait is always up to you."],
  live_stats: ["आमचे अंदाज, खऱ्या भावाशी तपासलेले", "हमारे अनुमान, असली भाव से जाँचे गए", "Our forecasts, checked against real prices"],
  others_title: ["FPO आणि खरेदीदारांसाठी", "FPO और ख़रीदारों के लिए", "For FPOs and buyers"],
  // buyer v2
  buy_sub: ["व्यापारी, प्रक्रिया उद्योग, निर्यातदार आणि FPO खरेदी विभागांसाठी — थेट शेतातून माल, योग्य भावात.", "व्यापारियों, प्रोसेसर, निर्यातकों और FPO ख़रीद के लिए — सीधे खेत से माल, सही भाव पर।", "For traders, processors, exporters and FPO procurement — produce straight from the farm at a fair price."],
  firm: ["नाव / फर्मचे नाव", "नाम / फ़र्म का नाम", "Name / firm name"],
  ws_only: ["फक्त घाऊक खरेदीदार · शुल्क 1%", "केवल थोक ख़रीदार · शुल्क 1%", "Wholesale buyers only · 1% fee"],
  below_fair: ["योग्य भावापेक्षा {n} कमी", "सही भाव से {n} कम", "{n} below fair price"],
  above_fair: ["योग्य भावापेक्षा {n} जास्त", "सही भाव से {n} ज़्यादा", "{n} above fair price"],
  listings_n: ["{n} लॉट उपलब्ध", "{n} लॉट उपलब्ध", "{n} lots available"],
  // fpo v2
  kpi_best: ["सर्वोत्तम मंडी भाव", "सबसे अच्छा मंडी भाव", "Best mandi price"],
  kpi_mandis: ["मंडी अंदाज", "मंडी अनुमान", "Mandis forecast"],
  kpi_stock: ["सदस्यांचा साठा", "सदस्यों का स्टॉक", "Member stock"],
  kpi_save: ["कारपूल बचत", "कारपूल बचत", "Carpool savings"],
  // fpo
  crop: ["पीक", "फसल", "Crop"],
  day: ["दिवस", "दिन", "Day"],
  today: ["आज", "आज", "Today"],
  in_days: ["{d} दिवसांनी", "{d} दिन बाद", "in {d} days"],
  map_title: ["मंडी भाव — 3D नकाशा", "मंडी भाव — 3D नक्शा", "Mandi prices — 3D map"],
  map_hint: ["खांबाची उंची = अपेक्षित ₹/क्विंटल. मंडीवर क्लिक करा.", "खंभे की ऊँचाई = अपेक्षित ₹/क्विंटल। मंडी पर क्लिक करें।", "Pillar height = expected ₹/quintal. Click a mandi."],
  conf_hi: ["खात्री जास्त", "भरोसा ज़्यादा", "High confidence"],
  conf_mid: ["मध्यम", "मध्यम", "Medium"],
  conf_lo: ["कमी", "कम", "Low"],
  nomap: ["या ब्राउझरमध्ये 3D नकाशा चालत नाही (WebGL नाही). खालील तक्ता वापरा.", "इस ब्राउज़र में 3D नक्शा नहीं चलता (WebGL नहीं)। नीचे की तालिका देखें।", "3D map unavailable in this browser (no WebGL). Use the table below."],
  fc_title: ["भाव अंदाज", "भाव अनुमान", "Price forecast"],
  horizon: ["कालावधी", "अवधि", "Horizon"],
  date: ["तारीख", "तारीख़", "Date"],
  mandi: ["मंडी", "मंडी", "Mandi"],
  per_qtl: ["₹/क्विंटल", "₹/क्विंटल", "₹/quintal"],
  range: ["शक्य पट्टा (P10–P90)", "संभावित दायरा (P10–P90)", "Likely range (P10–P90)"],
  expected: ["अपेक्षित (P50)", "अपेक्षित (P50)", "Expected (P50)"],
  live_title: ["थेट: शेतकऱ्यांचे प्रश्न", "लाइव: किसानों के सवाल", "Live: farmer queries"],
  live_sub: ["नाव/फोन लपवलेले · दर 15 सेकंदांनी", "नाम/फ़ोन छिपे · हर 15 सेकंड", "anonymised · refreshes every 15 s"],
  sell_now: ["आता विका", "अभी बेचें", "Sell now"],
  hold: ["थांबा", "रुकें", "Hold"],
  near: ["जवळ", "के पास", "near"],
  ago_m: ["{n} मि. पूर्वी", "{n} मि. पहले", "{n} min ago"],
  ago_h: ["{n} तास पूर्वी", "{n} घंटे पहले", "{n} h ago"],
  tr_title: ["अंदाज अचूकता (पीकनिहाय)", "अनुमान सटीकता (फसलवार)", "Forecast accuracy by crop"],
  tr_err: ["चूक %", "त्रुटि %", "Error %"],
  tr_in: ["पट्ट्यात %", "दायरे में %", "Inside %"],
  cp_title: ["एकत्र वाहतूक (कारपूल)", "साझा ढुलाई (कारपूल)", "Carpool suggestions"],
  farmers: ["शेतकरी", "किसान", "farmers"],
  total_qty: ["एकूण", "कुल", "Total"],
  saving: ["बचत", "बचत", "Saving"],
  span: ["अंतर", "दूरी", "span"],
  vehicle: ["वाहन", "वाहन", "Vehicle"],
  st_title: ["सदस्यांचा साठा", "सदस्यों का स्टॉक", "Member stock"],
  qty: ["प्रमाण (क्विंटल)", "मात्रा (क्विंटल)", "Qty (qtl)"],
  district: ["जिल्हा", "ज़िला", "District"],
  condition: ["दर्जा (फोटोवरून)", "हालत (फ़ोटो से)", "Condition (photo)"],
  spoil: ["नासाडी धोका", "ख़राबी जोखिम", "Spoilage risk"],
  per_day: ["/दिवस", "/दिन", "/day"],
  ready: ["तयार तारीख", "तैयार तारीख़", "Ready"],
  good: ["चांगला", "अच्छा", "Good"],
  fair: ["ठीक", "ठीक", "Fair"],
  poor: ["कमी", "कमज़ोर", "Poor"],
  none: ["अजून माहिती नाही", "अभी कोई डेटा नहीं", "No data yet"],
  // buyer
  buy_title: ["थेट शेतकऱ्याकडून घाऊक खरेदी", "सीधे किसान से थोक ख़रीद", "Wholesale, direct from farmers"],
  fee: ["सेल-स्मार्ट शुल्क: शेतकऱ्याकडून 1% + खरेदीदाराकडून 1% (पारंपरिक अडत 6–8%)", "सेल-स्मार्ट शुल्क: किसान से 1% + ख़रीदार से 1% (पारंपरिक आढ़त 6–8%)", "Sell Smart fee: 1% from farmer + 1% from buyer (vs 6–8% traditional commission)"],
  reg_title: ["एकदाच नोंदणी करा", "एक बार रजिस्टर करें", "Register once"],
  name: ["नाव", "नाम", "Name"],
  type: ["प्रकार", "प्रकार", "Type"],
  wholesale: ["घाऊक", "थोक", "Wholesale"],
  phone: ["मोबाईल नंबर", "मोबाइल नंबर", "Mobile number"],
  location: ["ठिकाण", "स्थान", "Location"],
  use_gps: ["माझे ठिकाण वापरा", "मेरा स्थान लें", "Use my location"],
  or_pin: ["किंवा पिनकोड", "या पिनकोड", "or pincode"],
  gps_ok: ["ठिकाण मिळाले ✓", "स्थान मिल गया ✓", "Location found ✓"],
  gps_fail: ["ठिकाण मिळाले नाही — पिनकोड टाका", "स्थान नहीं मिला — पिनकोड डालें", "Couldn't get location — enter pincode"],
  bad_pin: ["हा पिनकोड सापडला नाही (महाराष्ट्र)", "यह पिनकोड नहीं मिला (महाराष्ट्र)", "Pincode not found (Maharashtra)"],
  bad_phone: ["10 अंकी मोबाईल नंबर टाका", "10 अंकों का मोबाइल नंबर डालें", "Enter a 10-digit mobile number"],
  need_loc: ["ठिकाण किंवा पिनकोड द्या", "स्थान या पिनकोड दें", "Share location or enter pincode"],
  register: ["नोंदणी करा", "रजिस्टर करें", "Register"],
  hello: ["नमस्कार, {n}", "नमस्ते, {n}", "Hello, {n}"],
  logout: ["बदला", "बदलें", "Change"],
  near_me: ["माझ्या जवळचा माल", "मेरे पास का माल", "Produce near me"],
  all_crops: ["सर्व पिके", "सभी फसलें", "All crops"],
  within: ["अंतर", "दूरी", "Within"],
  any_km: ["कितीही", "कोई भी", "Any"],
  ask: ["शेतकऱ्याचा भाव", "किसान का भाव", "Asking"],
  fair_today: ["आजचा योग्य भाव", "आज का सही भाव", "Fair price today"],
  km_away: ["{n} किमी", "{n} किमी", "{n} km"],
  offer: ["ऑफर द्या", "ऑफ़र दें", "Make offer"],
  your_price: ["तुमचा भाव (₹/क्विंटल)", "आपका भाव (₹/क्विंटल)", "Your price (₹/quintal)"],
  send: ["पाठवा", "भेजें", "Send"],
  cancel: ["रद्द", "रद्द", "Cancel"],
  total: ["एकूण रक्कम", "कुल रकम", "Total"],
  fee_amt: ["तुमचे 1% शुल्क", "आपका 1% शुल्क", "Your 1% fee"],
  my_offers: ["माझ्या ऑफर", "मेरे ऑफ़र", "My offers"],
  status_sent: ["पाठवली", "भेजा", "Sent"],
  status_accepted: ["स्वीकारली", "स्वीकार", "Accepted"],
  status_rejected: ["नाकारली", "अस्वीकार", "Rejected"],
  contact: ["शेतकरी संपर्क", "किसान संपर्क", "Farmer contact"],
  offer_sent: ["ऑफर पाठवली ✓", "ऑफ़र भेजा ✓", "Offer sent ✓"],
  failed: ["काहीतरी चुकले, पुन्हा प्रयत्न करा", "कुछ गड़बड़, फिर कोशिश करें", "Something went wrong, try again"],
  qtl: ["क्विं.", "क्विं.", "qtl"],
};
const CROPS = {
  "Onion": ["कांदा", "प्याज", "Onion"], "Tomato": ["टोमॅटो", "टमाटर", "Tomato"], "Soyabean": ["सोयाबीन", "सोयाबीन", "Soyabean"],
  "Wheat": ["गहू", "गेहूं", "Wheat"], "Bengal Gram (Gram)(Whole)": ["हरभरा", "चना", "Gram (Chana)"], "Potato": ["बटाटा", "आलू", "Potato"],
  "Maize": ["मका", "मक्का", "Maize"], "Pomegranate": ["डाळिंब", "अनार", "Pomegranate"], "Grapes": ["द्राक्षे", "अंगूर", "Grapes"],
  "Garlic": ["लसूण", "लहसुन", "Garlic"], "Cotton": ["कापूस", "कपास", "Cotton"], "Jowar (Sorghum)": ["ज्वारी", "ज्वार", "Jowar"],
  "Bajra (Pearl Millet/Cumbu)": ["बाजरी", "बाजरा", "Bajra"], "Arhar (Tur/Red Gram)(Whole)": ["तूर", "अरहर", "Tur"],
  "Cabbage": ["कोबी", "पत्ता गोभी", "Cabbage"], "Cauliflower": ["फ्लॉवर", "फूलगोभी", "Cauliflower"], "Brinjal": ["वांगी", "बैंगन", "Brinjal"],
  "Green Chilli": ["हिरवी मिरची", "हरी मिर्च", "Green chilli"], "Banana": ["केळी", "केला", "Banana"],
};
const CROP_ICON = { "Onion": "🧅", "Tomato": "🍅", "Soyabean": "🫘", "Wheat": "🌾", "Bengal Gram (Gram)(Whole)": "🫛", "Potato": "🥔",
  "Maize": "🌽", "Pomegranate": "🍎", "Grapes": "🍇", "Garlic": "🧄", "Cotton": "☁️", "Banana": "🍌", "Green Chilli": "🌶️",
  "Brinjal": "🍆", "Cabbage": "🥬", "Cauliflower": "🥦" };
const cropIcon = c => CROP_ICON[c] || "🌱";
const DISTRICTS = { "Pune": ["पुणे", "पुणे"], "Nashik": ["नाशिक", "नासिक"], "Ahmednagar": ["अहिल्यानगर", "अहिल्यानगर"], "Ahilyanagar": ["अहिल्यानगर", "अहिल्यानगर"] };
const LANGS = ["mr", "hi", "en"];

let LANG = "mr";
try { LANG = localStorage.getItem("ss_lang") || "mr"; } catch (e) {}
if (!LANGS.includes(LANG)) LANG = "mr";
const li = () => LANGS.indexOf(LANG);

function t(k, vars) {
  let s = (STR[k] || [k, k, k])[li()];
  for (const v in vars || {}) s = s.replace("{" + v + "}", vars[v]);
  return s;
}
const cropName = c => (CROPS[c] || [c, c, c])[li()];
const districtName = d => LANG === "en" ? d : ((DISTRICTS[d] || [d, d])[li()]);
const mandiName = m => !m ? "" : LANG === "mr" ? (m.name_mr || m.market) : LANG === "hi" ? (m.name_hi || m.market) : m.market;

const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const rs = n => n == null || isNaN(n) ? "—" : "₹" + inr.format(Math.round(n));
const num = n => n == null || isNaN(n) ? "—" : inr.format(n);
const fmtDate = d => d ? new Date(d + (d.length === 10 ? "T00:00:00" : "")).toLocaleDateString(LANG + "-IN-u-nu-latn", { day: "numeric", month: "short" }) : "—";
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = s => document.querySelector(s);

// GET /api/<name>?<params>; on any failure fall back to /app/mock/<name>.json (filtered by crop) and show the demo badge.
async function api(name, params = {}) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== "")).toString();
  try {
    const r = await fetch("/api/" + name + (q ? "?" + q : ""));
    if (!r.ok) throw new Error(r.status);
    return await r.json();
  } catch (e) {
    const el = $("#demo"); if (el) el.classList.add("on");
    const rows = await (await fetch("/app/mock/" + name + ".json")).json();
    // ponytail: mock rows carry commodity/crop so one file serves every crop filter
    return params.crop && Array.isArray(rows) ? rows.filter(r => (r.commodity || r.crop) === params.crop) : rows;
  }
}

async function post(name, body) {
  const r = await fetch("/api/" + name, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}

// Apply static strings + language buttons; call onChange on every switch so pages re-render dynamic parts.
function initLang(onChange) {
  const apply = () => {
    document.documentElement.lang = LANG;
    document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
    document.querySelectorAll(".langs button").forEach(b => b.setAttribute("aria-pressed", b.dataset.lang === LANG));
  };
  document.querySelectorAll(".langs button").forEach(b => b.onclick = () => {
    LANG = b.dataset.lang;
    try { localStorage.setItem("ss_lang", LANG); } catch (e) {}
    apply(); onChange && onChange();
  });
  apply();
}

function store(k, v) {
  try { if (v === undefined) return JSON.parse(localStorage.getItem(k)); v === null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)); }
  catch (e) { return null; }
}
