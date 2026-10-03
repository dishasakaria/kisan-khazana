// Kisaan Khazana FPO dashboard — every user-facing string in मराठी / हिंदी / English. Order: [mr, hi, en].
const S = {
  brand: ["किसान खजाना", "किसान खज़ाना", "Kisaan Khazana"],
  tag: ["FPO डॅशबोर्ड", "FPO डैशबोर्ड", "FPO dashboard"],
  // nav
  overview: ["आढावा", "अवलोकन", "Overview"], inventory: ["साठा", "भंडार", "Inventory"], farmers: ["शेतकरी", "किसान", "Farmers"],
  lots: ["FPO लॉट", "FPO लॉट", "FPO Lots"], offers: ["खरेदीदार ऑफर", "ख़रीदार ऑफ़र", "Buyer Offers"],
  transactions: ["व्यवहार", "लेन-देन", "Transactions"], reports: ["अहवाल", "रिपोर्ट", "Reports"], settings: ["सेटिंग्ज", "सेटिंग", "Settings"],
  logout: ["बाहेर पडा", "लॉग आउट", "Log out"], menu: ["मेनू", "मेन्यू", "Menu"], close: ["बंद करा", "बंद करें", "Close"],
  notifications: ["सूचना", "सूचनाएँ", "Notifications"], no_notifications: ["नवीन काही नाही", "कुछ नया नहीं", "Nothing new"],
  refresh: ["रिफ्रेश", "रिफ़्रेश", "Refresh"], updated: ["अद्ययावत", "अपडेट", "Updated"],
  // auth
  login: ["लॉगिन", "लॉगिन", "Log in"], register: ["नवीन FPO नोंदणी", "नया FPO पंजीकरण", "Register your FPO"],
  phone_or_email: ["फोन किंवा ईमेल", "फ़ोन या ईमेल", "Phone or email"], password: ["पासवर्ड", "पासवर्ड", "Password"],
  password_hint: ["किमान 8 अक्षरे", "कम से कम 8 अक्षर", "At least 8 characters"],
  login_sub: ["तुमच्या FPO च्या साठ्याचे लॉट बनवा, खरेदीदारांच्या ऑफर स्वीकारा.", "अपने FPO के भंडार से लॉट बनाएँ, ख़रीदारों की ऑफ़र स्वीकारें।", "Turn your members' produce into lots and accept buyer offers."],
  no_account: ["खाते नाही?", "खाता नहीं है?", "No account yet?"], have_account: ["आधीच खाते आहे?", "पहले से खाता है?", "Already registered?"],
  fpo_name: ["FPO चे नाव", "FPO का नाम", "FPO name"], phone: ["फोन", "फ़ोन", "Phone"], email: ["ईमेल (ऐच्छिक)", "ईमेल (वैकल्पिक)", "Email (optional)"],
  address: ["पत्ता / पिकअप ठिकाण", "पता / पिकअप स्थान", "Address / pickup point"], district: ["जिल्हा", "ज़िला", "District"],
  location: ["ठिकाण", "स्थान", "Location"], lat: ["अक्षांश", "अक्षांश", "Latitude"], lon: ["रेखांश", "देशांतर", "Longitude"],
  use_gps: ["माझे ठिकाण वापरा", "मेरी लोकेशन लें", "Use my location"], gps_fail: ["ठिकाण मिळाले नाही — अक्षांश/रेखांश लिहा", "लोकेशन नहीं मिली — अक्षांश/देशांतर लिखें", "Location unavailable — enter latitude/longitude"],
  create_account: ["खाते तयार करा", "खाता बनाएँ", "Create account"], signing_in: ["लॉगिन होत आहे…", "लॉगिन हो रहा है…", "Signing in…"],
  // overview
  good_morning: ["सुप्रभात", "सुप्रभात", "Good morning"], good_afternoon: ["नमस्कार", "नमस्कार", "Good afternoon"], good_evening: ["शुभ संध्या", "शुभ संध्या", "Good evening"],
  action_required: ["{n} खरेदीदार ऑफर तुमच्या उत्तराची वाट पाहत आहेत", "{n} ख़रीदार ऑफ़र आपके जवाब की प्रतीक्षा में हैं", "{n} buyer offers need your response"],
  action_required_1: ["1 खरेदीदार ऑफर तुमच्या उत्तराची वाट पाहत आहे", "1 ख़रीदार ऑफ़र आपके जवाब की प्रतीक्षा में है", "1 buyer offer needs your response"],
  review_offers: ["ऑफर पहा", "ऑफ़र देखें", "Review offers"],
  m_available: ["उपलब्ध माल", "उपलब्ध माल", "Available produce"], m_open_lots: ["खुले लॉट", "खुले लॉट", "Open lots"],
  m_pending: ["प्रलंबित ऑफर", "लंबित ऑफ़र", "Pending offers"], m_sold_month: ["या महिन्यात विकले", "इस महीने बिका", "Sold this month"],
  in_lots: ["लॉटमध्ये", "लॉट में", "in lots"], drafts: ["मसुदे", "ड्राफ़्ट", "drafts"],
  current_inventory: ["सध्याचा साठा (पिकानुसार)", "वर्तमान भंडार (फसल अनुसार)", "Current inventory by crop"],
  recent_offers: ["अलीकडील ऑफर", "हाल की ऑफ़र", "Recent offers"], active_lots: ["सक्रिय लॉट", "सक्रिय लॉट", "Active lots"],
  quick_actions: ["त्वरित कृती", "त्वरित कार्य", "Quick actions"], create_lot: ["लॉट तयार करा", "लॉट बनाएँ", "Create lot"],
  view_offers: ["ऑफर पहा", "ऑफ़र देखें", "View offers"], view_all: ["सर्व पहा", "सभी देखें", "View all"],
  // tables / fields
  crop: ["पीक", "फसल", "Crop"], total: ["एकूण", "कुल", "Total"], available: ["उपलब्ध", "उपलब्ध", "Available"], qty: ["प्रमाण", "मात्रा", "Quantity"],
  qtl: ["क्विं", "क्विं", "qtl"], quintal: ["क्विंटल", "क्विंटल", "quintal"], farmers_n: ["शेतकरी", "किसान", "Farmers"], status: ["स्थिती", "स्थिति", "Status"],
  updated_at: ["अद्ययावत", "अपडेट", "Updated"], name: ["नाव", "नाम", "Name"], village: ["गाव / जवळचे शहर", "गाँव / पास का शहर", "Village / nearest town"],
  primary_crop: ["मुख्य पीक", "मुख्य फसल", "Primary crop"], via_telegram: ["Telegram द्वारे", "Telegram से", "via Telegram"], via_sms: ["SMS द्वारे", "SMS से", "via SMS"], via_call: ["कॉल द्वारे", "कॉल से", "via call"],
  condition: ["दर्जा", "हालत", "Condition"], ready: ["तयार", "तैयार", "Ready"], farmer: ["शेतकरी", "किसान", "Farmer"], channel: ["माध्यम", "माध्यम", "Channel"],
  lot: ["लॉट", "लॉट", "Lot"], lot_id: ["लॉट क्र.", "लॉट नं.", "Lot ID"], asking_price: ["मागणी भाव", "माँग भाव", "Asking price"],
  market_ref: ["बाजार संदर्भ भाव", "बाज़ार संदर्भ भाव", "Market reference"], quality: ["गुणवत्ता", "गुणवत्ता", "Quality"],
  pickup: ["पिकअप ठिकाण", "पिकअप स्थान", "Pickup location"], notes: ["नोंदी", "नोट्स", "Notes"], created: ["तयार केले", "बनाया", "Created"],
  buyer: ["खरेदीदार", "ख़रीदार", "Buyer"], company: ["कंपनी", "कंपनी", "Company"], type: ["प्रकार", "प्रकार", "Type"], price: ["भाव", "भाव", "Price"],
  per_qtl: ["/क्विं", "/क्विं", "/qtl"], total_value: ["एकूण रक्कम", "कुल राशि", "Total value"], buyer_fee: ["खरेदीदार शुल्क (1%)", "ख़रीदार शुल्क (1%)", "Buyer fee (1%)"],
  submitted: ["पाठवले", "भेजा", "Submitted"], decided: ["निर्णय", "निर्णय", "Decided"], date: ["दिनांक", "दिनांक", "Date"], sold: ["विकले", "बिका", "Sold"],
  pending_offers_n: ["प्रलंबित ऑफर", "लंबित ऑफ़र", "Pending offers"], contributors: ["योगदान देणारे शेतकरी", "योगदान देने वाले किसान", "Contributing farmers"],
  items: ["नोंदी", "प्रविष्टियाँ", "Entries"], contact: ["संपर्क", "संपर्क", "Contact"], call: ["कॉल", "कॉल", "Call"], whatsapp: ["WhatsApp", "WhatsApp", "WhatsApp"],
  // statuses (always text)
  st_open: ["उपलब्ध", "उपलब्ध", "Available"], st_in_lot: ["लॉटमध्ये", "लॉट में", "In lot"], st_sold: ["विकले", "बिका", "Sold"],
  st_available: ["उपलब्ध", "उपलब्ध", "Available"], st_draft: ["मसुदा", "ड्राफ़्ट", "Draft"], st_lot_open: ["खुला", "खुला", "Open"],
  st_closed: ["बंद", "बंद", "Closed"], st_sent: ["प्रलंबित", "लंबित", "Pending"], st_accepted: ["स्वीकारले", "स्वीकृत", "Accepted"], st_rejected: ["नाकारले", "अस्वीकृत", "Rejected"],
  t_wholesale: ["घाऊक व्यापारी", "थोक व्यापारी", "Wholesaler"], t_processor: ["प्रक्रिया उद्योग", "प्रोसेसर", "Processor"], t_exporter: ["निर्यातदार", "निर्यातक", "Exporter"], t_fpo: ["FPO खरेदी", "FPO ख़रीद", "FPO procurement"],
  // tabs / filters
  all: ["सर्व", "सभी", "All"], new: ["नवीन", "नया", "New"], pending: ["प्रलंबित", "लंबित", "Pending"], accepted: ["स्वीकारले", "स्वीकृत", "Accepted"], rejected: ["नाकारले", "अस्वीकृत", "Rejected"],
  open: ["खुले", "खुले", "Open"], draft: ["मसुदा", "ड्राफ़्ट", "Draft"], closed: ["बंद", "बंद", "Closed"],
  search: ["शोधा", "खोजें", "Search"], all_crops: ["सर्व पिके", "सभी फसलें", "All crops"], all_status: ["सर्व स्थिती", "सभी स्थिति", "All statuses"],
  prev: ["मागे", "पिछला", "Previous"], next: ["पुढे", "अगला", "Next"], page_of: ["पान {p} / {n}", "पृष्ठ {p} / {n}", "Page {p} of {n}"], results: ["{n} निकाल", "{n} परिणाम", "{n} results"],
  // actions
  publish: ["प्रकाशित करा", "प्रकाशित करें", "Publish"], unpublish: ["थांबवा (मसुदा)", "रोकें (ड्राफ़्ट)", "Pause (draft)"], close_lot: ["लॉट बंद करा", "लॉट बंद करें", "Close lot"],
  edit: ["संपादन", "संपादित करें", "Edit"], save: ["जतन करा", "सहेजें", "Save"], cancel: ["रद्द", "रद्द", "Cancel"], accept: ["स्वीकारा", "स्वीकारें", "Accept"], reject: ["नाकारा", "अस्वीकार करें", "Reject"],
  confirm: ["पुष्टी करा", "पुष्टि करें", "Confirm"], back: ["मागे", "वापस", "Back"], details: ["तपशील", "विवरण", "Details"], working: ["प्रक्रिया सुरू…", "प्रक्रिया जारी…", "Working…"],
  confirm_accept: ["ही ऑफर स्वीकारायची?", "यह ऑफ़र स्वीकार करें?", "Accept this offer?"],
  confirm_accept_body: ["{q} क्विंटल {c} ₹{p}/क्विंटल दराने {b} ला विकले जाईल (एकूण {t}). खरेदीदाराला तुमचा फोन दिसेल.", "{q} क्विंटल {c} ₹{p}/क्विंटल पर {b} को बिकेगा (कुल {t})। ख़रीदार को आपका फ़ोन दिखेगा।", "{q} qtl of {c} will be sold to {b} at ₹{p}/qtl (total {t}). The buyer will see your FPO's phone number."],
  confirm_reject: ["ही ऑफर नाकारायची?", "यह ऑफ़र अस्वीकार करें?", "Reject this offer?"],
  confirm_reject_body: ["{b} ची {q} क्विंटल ऑफर नाकारली जाईल. हे परत करता येणार नाही.", "{b} की {q} क्विंटल ऑफ़र अस्वीकार होगी। इसे पलटा नहीं जा सकता।", "{b}'s offer for {q} qtl will be rejected. This cannot be undone."],
  confirm_close: ["हा लॉट बंद करायचा?", "यह लॉट बंद करें?", "Close this lot?"],
  confirm_close_body: ["प्रलंबित ऑफर नाकारल्या जातील. काहीही विकले नसल्यास माल साठ्यात परत जाईल.", "लंबित ऑफ़र अस्वीकार होंगी। कुछ न बिका हो तो माल भंडार में लौट जाएगा।", "Pending offers will be rejected. If nothing was sold, the stock returns to inventory."],
  confirm_publish: ["लॉट प्रकाशित करायचा?", "लॉट प्रकाशित करें?", "Publish this lot?"],
  confirm_publish_body: ["खरेदीदारांना हा लॉट किसान खजाना अ‍ॅपमध्ये दिसेल.", "ख़रीदारों को यह लॉट किसान खज़ाना ऐप में दिखेगा।", "Buyers will see this lot in the Kisaan Khazana app."],
  confirm_unpublish: ["लॉट थांबवायचा?", "लॉट रोकें?", "Pause this lot?"],
  confirm_unpublish_body: ["लॉट खरेदीदारांपासून लपवला जाईल (मसुदा). नंतर पुन्हा प्रकाशित करता येईल.", "लॉट ख़रीदारों से छिप जाएगा (ड्राफ़्ट)। बाद में फिर प्रकाशित कर सकते हैं।", "The lot is hidden from buyers (draft). You can publish it again later."],
  done_accept: ["ऑफर स्वीकारली. लॉटमध्ये {a} क्विंटल शिल्लक.", "ऑफ़र स्वीकृत। लॉट में {a} क्विंटल बाकी।", "Offer accepted. {a} qtl left in the lot."],
  done_reject: ["ऑफर नाकारली.", "ऑफ़र अस्वीकृत।", "Offer rejected."], done_saved: ["जतन केले.", "सहेजा गया।", "Saved."],
  done_publish: ["लॉट प्रकाशित झाला.", "लॉट प्रकाशित हुआ।", "Lot published."], done_unpublish: ["लॉट थांबवला.", "लॉट रोका गया।", "Lot paused."], done_close: ["लॉट बंद केला.", "लॉट बंद हुआ।", "Lot closed."],
  // create lot wizard
  new_lot: ["नवीन लॉट", "नया लॉट", "New lot"], step_crop: ["पीक", "फसल", "Crop"], step_items: ["माल निवडा", "माल चुनें", "Pick stock"], step_price: ["भाव", "भाव", "Price"], step_details: ["तपशील", "विवरण", "Details"],
  choose_crop: ["कोणत्या पिकाचा लॉट?", "किस फसल का लॉट?", "Which crop is this lot for?"],
  pick_items: ["लॉटमध्ये कोणता माल घ्यायचा?", "लॉट में कौन सा माल लें?", "Which stock goes into the lot?"],
  pick_items_hint: ["प्रत्येक नोंद पूर्ण प्रमाणासह लॉटमध्ये जाते.", "हर प्रविष्टि पूरी मात्रा के साथ लॉट में जाती है।", "Each stock entry goes into the lot with its full quantity."],
  selected_total: ["निवडलेले: {n} नोंदी, {q} क्विंटल", "चुना: {n} प्रविष्टियाँ, {q} क्विंटल", "Selected: {n} entries, {q} qtl"],
  set_price: ["मागणी भाव ठरवा (₹/क्विंटल)", "माँग भाव तय करें (₹/क्विंटल)", "Set the asking price (₹/qtl)"],
  ref_from: ["आजचा मॉडेल भाव {m} मंडी, {d}: ₹{p}/क्विंटल", "आज का मॉडल भाव {m} मंडी, {d}: ₹{p}/क्विंटल", "Today's model price at {m} mandi ({d}): ₹{p}/qtl"],
  ref_none: ["या पिकासाठी संदर्भ भाव उपलब्ध नाही.", "इस फसल के लिए संदर्भ भाव उपलब्ध नहीं।", "No market reference price available for this crop."],
  use_ref: ["संदर्भ भाव वापरा", "संदर्भ भाव लें", "Use reference price"],
  lot_value: ["अंदाजे लॉट मूल्य", "अनुमानित लॉट मूल्य", "Estimated lot value"],
  quality_ph: ["उदा. Grade A, 55 mm+", "जैसे Grade A, 55 mm+", "e.g. Grade A, 55 mm+"], notes_ph: ["खरेदीदारासाठी नोंदी", "ख़रीदार के लिए नोट्स", "Notes for the buyer"],
  pickup_ph: ["रिकामे ठेवल्यास FPO चा पत्ता", "खाली छोड़ें तो FPO का पता", "Leave empty to use the FPO address"],
  save_draft: ["मसुदा म्हणून जतन करा", "ड्राफ़्ट सहेजें", "Save as draft"], create_publish: ["तयार करा आणि प्रकाशित करा", "बनाएँ और प्रकाशित करें", "Create and publish"],
  no_stock_for_lot: ["लॉटसाठी उपलब्ध माल नाही. शेतकरी Telegram वर \"FPO ला द्या\" दाबल्यावर माल इथे येतो.", "लॉट के लिए उपलब्ध माल नहीं। किसान Telegram पर \"FPO को दें\" दबाएँ तो माल यहाँ आता है।", "No available stock to make a lot. Stock arrives here when a member taps \"Give to FPO\" on Telegram."],
  lot_created: ["लॉट {c} तयार झाला.", "लॉट {c} बन गया।", "Lot {c} created."],
  edit_lot: ["लॉट संपादन", "लॉट संपादन", "Edit lot"],
  // empty states
  empty_inventory: ["अजून साठा नाही", "अभी भंडार नहीं", "No inventory yet"],
  empty_inventory_sub: ["सदस्य शेतकऱ्यांनी Telegram वर \"FPO ला द्या\" दाबले की त्यांचा माल इथे दिसेल.", "सदस्य किसान Telegram पर \"FPO को दें\" दबाएँगे तो उनका माल यहाँ दिखेगा।", "When member farmers tap \"Give to FPO\" on Telegram, their stock shows up here."],
  empty_farmers: ["अजून सदस्य नाहीत", "अभी सदस्य नहीं", "No members yet"],
  empty_farmers_sub: ["तुमच्या FPO च्या 60 किमी आत असलेला शेतकरी माल देताच सदस्य होतो.", "आपके FPO के 60 किमी के भीतर का किसान माल देते ही सदस्य बनता है।", "A farmer within 60 km of your FPO becomes a member the moment they give stock."],
  empty_lots: ["अजून लॉट नाहीत", "अभी लॉट नहीं", "No lots yet"], empty_lots_sub: ["साठ्यातून पहिला लॉट तयार करा.", "भंडार से पहला लॉट बनाएँ।", "Create your first lot from inventory."],
  empty_offers: ["अजून ऑफर नाहीत", "अभी ऑफ़र नहीं", "No offers yet"], empty_offers_sub: ["लॉट प्रकाशित झाल्यावर खरेदीदारांच्या ऑफर इथे येतात.", "लॉट प्रकाशित होने पर ख़रीदारों की ऑफ़र यहाँ आती हैं।", "Buyer offers arrive here once a lot is published."],
  empty_tx: ["अजून व्यवहार नाहीत", "अभी लेन-देन नहीं", "No transactions yet"], empty_tx_sub: ["स्वीकारलेली प्रत्येक ऑफर इथे व्यवहार म्हणून दिसते.", "हर स्वीकृत ऑफ़र यहाँ लेन-देन के रूप में दिखती है।", "Every accepted offer appears here as a transaction."],
  empty_reports: ["अजून पुरेसा डेटा नाही", "अभी पर्याप्त डेटा नहीं", "Not enough data yet"], empty_reports_sub: ["पहिली ऑफर स्वीकारल्यावर अहवाल तयार होतील.", "पहली ऑफ़र स्वीकारने पर रिपोर्ट बनेगी।", "Reports appear after your first accepted offer."],
  empty_filter: ["या फिल्टरसाठी काही नाही", "इस फ़िल्टर के लिए कुछ नहीं", "Nothing matches this filter"],
  not_found: ["सापडले नाही", "नहीं मिला", "Not found"],
  // reports
  r_qty: ["विकलेले प्रमाण", "बिकी मात्रा", "Quantity sold"], r_value: ["एकूण मूल्य", "कुल मूल्य", "Total value"], r_avg: ["सरासरी भाव", "औसत भाव", "Average price"], r_deals: ["व्यवहार", "सौदे", "Deals"],
  r_by_crop: ["पिकानुसार विक्री", "फसल अनुसार बिक्री", "Sales by crop"], r_by_month: ["महिन्यानुसार", "महीने अनुसार", "By month"], r_farmers: ["शेतकऱ्यांचे योगदान", "किसानों का योगदान", "Farmer contribution"],
  lots_sold: ["लॉट विकले", "लॉट बिके", "lots sold"],
  r_buyers: ["प्रमुख खरेदीदार", "प्रमुख ख़रीदार", "Top buyers"], given: ["दिलेला माल", "दिया माल", "Given"], in_sold: ["विकलेल्या लॉटमध्ये", "बिके लॉट में", "In sold lots"],
  // settings
  profile: ["FPO प्रोफाइल", "FPO प्रोफ़ाइल", "FPO profile"], language: ["भाषा", "भाषा", "Language"], new_password: ["नवीन पासवर्ड (बदलायचा असल्यास)", "नया पासवर्ड (बदलना हो तो)", "New password (only to change it)"],
  account: ["खाते", "खाता", "Account"], member_since: ["नोंदणी", "पंजीकरण", "Registered"], about: ["किसान खजाना — खरेदीदार फक्त FPO कडून खरेदी करतात. शेतकऱ्यांची माहिती खरेदीदारांना कधीही दिसत नाही.", "किसान खज़ाना — ख़रीदार सिर्फ़ FPO से ख़रीदते हैं। किसानों की जानकारी ख़रीदारों को कभी नहीं दिखती।", "Kisaan Khazana — buyers buy only from FPOs. Farmer details are never shown to buyers."],
  // errors (human text for API codes)
  e_network: ["सर्व्हरशी संपर्क होत नाही. इंटरनेट तपासून पुन्हा प्रयत्न करा.", "सर्वर से संपर्क नहीं हो रहा। इंटरनेट जाँचकर फिर कोशिश करें।", "Can't reach the server. Check your connection and try again."],
  e_timeout: ["सर्व्हरने वेळेत उत्तर दिले नाही. पुन्हा प्रयत्न करा.", "सर्वर ने समय पर जवाब नहीं दिया। फिर कोशिश करें।", "The server took too long to respond. Please try again."],
  e_401: ["सत्र संपले. पुन्हा लॉगिन करा.", "सत्र समाप्त। फिर लॉगिन करें।", "Your session has expired. Please log in again."],
  e_403: ["याची परवानगी नाही.", "इसकी अनुमति नहीं।", "You don't have permission to do that."],
  e_404: ["हे आता उपलब्ध नाही किंवा तुमच्या FPO चे नाही.", "यह अब उपलब्ध नहीं या आपके FPO का नहीं।", "That item no longer exists or doesn't belong to your FPO."],
  e_422: ["काही माहिती चुकीची आहे. तपासून पुन्हा पाठवा.", "कुछ जानकारी गलत है। जाँचकर फिर भेजें।", "Some of the details are invalid. Please check and resend."],
  e_429: ["खूप प्रयत्न झाले. थोड्या वेळाने पुन्हा करा.", "बहुत कोशिशें हुईं। थोड़ी देर बाद करें।", "Too many attempts. Please wait a while and try again."],
  e_500: ["सर्व्हरमध्ये त्रुटी. थोड्या वेळाने पुन्हा करा.", "सर्वर में त्रुटि। थोड़ी देर बाद करें।", "Something went wrong on the server. Please try again shortly."],
  e_bad_login: ["फोन/ईमेल किंवा पासवर्ड चुकीचा.", "फ़ोन/ईमेल या पासवर्ड गलत।", "Wrong phone/email or password."],
  e_bad_password: ["पासवर्ड किमान 8 अक्षरांचा हवा.", "पासवर्ड कम से कम 8 अक्षर का हो।", "Password must be at least 8 characters."],
  e_bad_phone: ["10 अंकी भारतीय मोबाइल नंबर द्या.", "10 अंकों का भारतीय मोबाइल नंबर दें।", "Enter a valid 10-digit Indian mobile number."],
  e_bad_email: ["ईमेल चुकीचा आहे.", "ईमेल गलत है।", "That email address looks wrong."],
  e_bad_name: ["नाव 2 ते 120 अक्षरांचे हवे.", "नाम 2 से 120 अक्षर का हो।", "Name must be 2 to 120 characters."],
  e_bad_location: ["ठिकाण भारतात हवे (अक्षांश/रेखांश).", "स्थान भारत में हो (अक्षांश/देशांतर)।", "Location must be in India (latitude/longitude)."],
  e_bad_price: ["भाव 0 पेक्षा जास्त आणि ₹1,00,000/क्विंटल पेक्षा कमी हवा.", "भाव 0 से ज़्यादा और ₹1,00,000/क्विंटल से कम हो।", "Price must be above 0 and under ₹1,00,000 per quintal."],
  e_bad_items: ["निवडलेला माल उपलब्ध नाही किंवा या FPO चा नाही.", "चुना माल उपलब्ध नहीं या इस FPO का नहीं।", "The selected stock isn't available or doesn't belong to this FPO."],
  e_mixed_crops: ["एका लॉटमध्ये एकच पीक घ्या.", "एक लॉट में एक ही फसल लें।", "A lot can hold only one crop."],
  e_items_taken: ["काही माल आधीच दुसऱ्या लॉटमध्ये गेला. पान रिफ्रेश करा.", "कुछ माल पहले ही दूसरे लॉट में चला गया। पेज रिफ़्रेश करें।", "Some of that stock just went into another lot. Refresh and try again."],
  e_duplicate: ["हा फोन/ईमेल आधीच नोंदलेला आहे.", "यह फ़ोन/ईमेल पहले से पंजीकृत है।", "That phone or email is already registered."],
  e_insufficient_qty: ["लॉटमध्ये आता इतका माल शिल्लक नाही.", "लॉट में अब इतना माल बाकी नहीं।", "That lot no longer has enough quantity available."],
  e_not_pending: ["या ऑफरवर आधीच निर्णय झाला आहे.", "इस ऑफ़र पर पहले ही निर्णय हो चुका है।", "This offer has already been decided."],
  e_lot_closed: ["हा लॉट बंद किंवा विकला गेला आहे.", "यह लॉट बंद या बिक चुका है।", "This lot is closed or sold out."],
  e_bad_status: ["या स्थितीत ही कृती करता येत नाही.", "इस स्थिति में यह कार्य नहीं हो सकता।", "That action isn't possible in the lot's current state."],
  e_pending_offers: ["आधी प्रलंबित ऑफरवर निर्णय घ्या, मग लॉट थांबवा.", "पहले लंबित ऑफ़र पर निर्णय लें, फिर लॉट रोकें।", "Decide the pending offers first, then pause the lot."],
  e_bad_input: ["माहिती तपासा.", "जानकारी जाँचें।", "Please check the details."],
  e_generic: ["काहीतरी चुकले. पुन्हा प्रयत्न करा.", "कुछ गलत हुआ। फिर कोशिश करें।", "Something went wrong. Please try again."],
  retry: ["पुन्हा प्रयत्न", "फिर कोशिश", "Try again"], loading: ["लोड होत आहे…", "लोड हो रहा है…", "Loading…"],
};

const CROPS = {
  mr: {"Onion": "कांदा", "Tomato": "टोमॅटो", "Soyabean": "सोयाबीन", "Wheat": "गहू", "Bengal Gram (Gram)(Whole)": "हरभरा", "Arhar (Tur/Red Gram)(Whole)": "तूर",
       "Potato": "बटाटा", "Pomegranate": "डाळिंब", "Grapes": "द्राक्ष", "Maize": "मका", "Jowar (Sorghum)": "ज्वारी", "Bajra (Pearl Millet/Cumbu)": "बाजरी", "Cotton": "कापूस"},
  hi: {"Onion": "प्याज", "Tomato": "टमाटर", "Soyabean": "सोयाबीन", "Wheat": "गेहूं", "Bengal Gram (Gram)(Whole)": "चना", "Arhar (Tur/Red Gram)(Whole)": "तूर",
       "Potato": "आलू", "Pomegranate": "अनार", "Grapes": "अंगूर", "Maize": "मक्का", "Jowar (Sorghum)": "ज्वार", "Bajra (Pearl Millet/Cumbu)": "बाजरा", "Cotton": "कपास"},
};
const SHORT = {"Bengal Gram (Gram)(Whole)": "Bengal Gram", "Arhar (Tur/Red Gram)(Whole)": "Arhar (Tur)", "Jowar (Sorghum)": "Jowar", "Bajra (Pearl Millet/Cumbu)": "Bajra"};
export const LANGS = [["mr", "मराठी"], ["hi", "हिंदी"], ["en", "English"]];
const IDX = {mr: 0, hi: 1, en: 2};

let lang = "mr";
try { lang = localStorage.getItem("kk_lang") || ((navigator.language || "").startsWith("hi") ? "hi" : "mr"); } catch (e) { /* storage blocked */ }
if (!IDX.hasOwnProperty(lang)) lang = "mr";

export const getLang = () => lang;
export function setLang(l) {
  if (!IDX.hasOwnProperty(l)) return;
  lang = l;
  try { localStorage.setItem("kk_lang", l); } catch (e) { /* storage blocked */ }
  document.documentElement.lang = l;
}
export function t(key, vars) {
  const row = S[key];
  let s = row ? row[IDX[lang]] : key;
  if (vars) for (const k in vars) s = s.split("{" + k + "}").join(vars[k]);
  return s;
}
export const cropName = (c) => (c && CROPS[lang] && CROPS[lang][c]) || SHORT[c] || c || "—";
export const locale = () => ({mr: "mr-IN", hi: "hi-IN", en: "en-IN"}[lang]);
