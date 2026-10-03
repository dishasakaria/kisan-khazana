"""Build data/ext/{events,msp,schemes}.csv for sell-smart. Every row's source_url was opened during research."""
import csv
from pathlib import Path

OUT = Path("/home/user/sell-smart/data/ext")
PIB = "https://www.pib.gov.in/PressReleasePage.aspx?PRID="
DG = "https://content.dgft.gov.in/Website/dgftprod/"
ON, WH, RI, SU, SO = "Onion", "Wheat", "Rice", "Sugar", "Soyabean"
TUR, GRAM, URAD, MASUR, MOONG = ("Arhar (Tur/Red Gram)(Whole)", "Bengal Gram (Gram)(Whole)",
                                 "Black Gram (Urd Beans)(Whole)", "Lentil (Masur)(Whole)", "Green Gram (Moong)(Whole)")
T, F = "true", "false"

# date_start, date_end, commodity, event_type, value, unit, description, source_url, verified
E = [
 # ---------------- ONION: export policy ----------------
 ("2019-09-13", "2019-09-28", ON, "min_export_price_usd_t", 850, "usd_per_t_fob", "MEP USD 850/t FOB, exports only against Letter of Credit (DGFT notification 13-09-2019); superseded by export ban 29-09-2019", "https://www.pib.gov.in/newsite/PrintRelease.aspx?relid=193190&reg=48&lang=2", T),
 ("2019-09-29", "2020-03-14", ON, "export_ban", 1, "flag", "All onion exports prohibited with immediate effect; lifted (made free, no LC/MEP) w.e.f. 15-03-2020", "https://www.businesstoday.in/latest/economy-politics/story/govt-bans-export-of-all-varieties-of-onions-price-touch-rs-80kg-229793-2019-09-29 | https://www.deccanherald.com/amp/story/business%2Fcentre-lifts-export-ban-on-onions-809970.html", T),
 ("2020-09-14", "2020-12-31", ON, "export_ban", 1, "flag", "DGFT Notif 31/2015-20 dt 14-09-2020 prohibits export of all onion varieties; export made free w.e.f. 01-01-2021", "https://e-startupindia.com/learn/dgft-issued-a-notification-for-export-policy-of-onion/ | https://www.thehawk.in/news/economy-and-business/govt-lifts-export-ban-on-all-varieties-of-onion-from-january-1-b82f5ae5-56dc-4aca-a6ab-aacf3c3d777d", T),
 ("2023-08-19", "2023-12-31", ON, "export_duty_pct", 40, "pct", "First-ever 40% export duty on onion (Customs notif 48/2023) till 31-12-2023; overtaken by export ban from 08-12-2023", "https://www.newsonair.gov.in/centre-imposes-40-percent-export-duty-on-onions-to-improve-its-domestic-availability | " + PIB + "2016405", T),
 ("2023-10-29", "2023-12-07", ON, "min_export_price_usd_t", 800, "usd_per_t_fob", "MEP USD 800/t FOB till 31-12-2023 (DGFT 42/2023 dt 28-10-2023, superseded by 45/2023 dt 23-11-2023); replaced by ban 08-12-2023", DG + "1f4b2c70-13f7-42d4-ac97-19443cb3ebbf/Notification%20No.%2045-2023-%20English.pdf | " + DG + "d73aebd9-ab58-4652-8987-607fa0cc69ef/DGFT%20Notification%20No%2042-2023%20dated%2028.10.2023-ENGLISH.pdf", T),
 ("2023-12-08", "2024-05-03", ON, "export_ban", 1, "flag", "Export prohibited till 31-03-2024 (DGFT 49/2023), extended 'until further orders' (DGFT 81/2023 dt 22-03-2024), lifted 04-05-2024 (DGFT 10/2024-25); limited G2G exports allowed to Bangladesh/UAE/Bhutan/Bahrain/Mauritius/Sri Lanka", DG + "7a0297d6-4c65-4129-8008-97dd3b5a7c28/Notification%20No%2049-2023-English.pdf | " + DG + "ed8d1d77-8aac-4860-a9f0-0c9efd81a9a8/Notification%20-English.pdf", T),
 ("2024-05-04", "2024-09-12", ON, "min_export_price_usd_t", 550, "usd_per_t", "Ban lifted; export Free subject to MEP USD 550/t (DGFT 10/2024-25); MEP removed by DGFT 28/2024-25 dt 13-09-2024", DG + "4b6e4af0-79f3-4a57-a00d-b869f956e12e/Notification%20No.%2010%202024-25-English.pdf | " + DG + "4df9632c-d01e-42d7-bc41-ce3079db2f99/Notification%2028%202024-25%20-English.pdf", T),
 ("2024-05-04", "2024-09-12", ON, "export_duty_pct", 40, "pct", "40% export duty imposed effective 04-05-2024 alongside lifting of ban", "https://www.deccanherald.com/amp/story/india%2Fgovt-imposes-40-export-duty-on-onion-effective-may-4-3007182", T),
 ("2024-09-13", "2025-03-31", ON, "export_duty_pct", 20, "pct", "Export duty cut 40% -> 20% from 13-09-2024; withdrawn w.e.f. 01-04-2025 (Customs notif 19/2025 dt 22-03-2025)", PIB + "2114060", T),
 ("2025-04-01", "", ON, "export_duty_pct", 0, "pct", "20% export duty withdrawn; no duty/MEP/ban on onion exports from 01-04-2025", PIB + "2114060", T),
 # ---------------- ONION: stock limits ----------------
 ("2019-09-29", "", ON, "stock_limit", 500, "qtl_wholesaler", "Stock limit with export ban: wholesalers 500 qtl, retailers 100 qtl (later revisions/end date not captured)", "https://thefederal.com/news/govt-bans-onion-export-imposes-stock-limit-on-traders-to-check-price-rise", T),
 ("2020-10-23", "2020-12-31", ON, "stock_limit", 25, "MT_wholesaler", "Stock limits under amended EC Act: wholesalers 25 t, retailers 2 t, till Dec 2020", "https://www.business-standard.com/article/economy-policy/centre-invokes-new-essential-commodities-act-to-set-stock-limits-on-onion-120102301345_1.html", T),
 # ---------------- ONION: NAFED/NCCF price-stabilisation buffer ----------------
 ("2019-12-30", "", ON, "buffer_procurement", 1.0, "LMT_target", "Centre decides to create 1 lakh t onion buffer for 2020 (rabi 2020 procurement)", "https://www.deccanherald.com/national/national-politics/govt-to-make-1-lakh-tons-of-onion-buffer-stock-in-2020-789918.html", T),
 ("2020-10-29", "", ON, "buffer_release", 1.0, "LMT", "1 lakh t buffer being released through NAFED amid price spike", "https://www.tribuneindia.com/news/nation/govt-releasing-one-lakh-tonne-of-onion-buffer-stock-tomar-162767/amp", T),
 ("2021-04-01", "2021-07-31", ON, "buffer_procurement", 2.0, "LMT_target", "NAFED plan for record 2 lakh t buffer in 2021 from 7 states incl. Maharashtra; DATES APPROXIMATE (rabi procurement season), article undated", "https://www.thehawk.in/news/economy-and-business/bumper-yield-of-onions-in-2021-centre-will-create-a-record-with-2-lakh-tons-buffer-stock-061a5c86-484d-4195-8feb-268488eb414c", F),
 ("2022-04-01", "2022-07-31", ON, "buffer_procurement", 2.51, "LMT", "Buffer maintained in FY2022-23 = 2.51 lakh t (reported Jul 2023); DATES APPROXIMATE", "https://www.tribuneindia.com/news/business/government-procures-3-lakh-tonnes-of-onion-for-buffer-stock-526191/amp", F),
 ("2023-02-24", "2023-03-07", ON, "buffer_procurement", 900, "rs_qtl_min_price", "NAFED intervention purchase of red (kharif) onion via 40 centres after Maharashtra modal price fell to Rs 500-700/qtl; ~4,000 t bought at > Rs 900/qtl", PIB + "1904936", T),
 ("2023-04-01", "2023-07-16", ON, "buffer_procurement", 3.0, "LMT", "3 lakh t rabi onion procured for buffer (20% more than prior year) - reported 16-07-2023; start date approx (since March per DH 22-08-2023)", "https://www.tribuneindia.com/news/business/government-procures-3-lakh-tonnes-of-onion-for-buffer-stock-526191/amp", F),
 ("2023-08-11", "", ON, "buffer_release", 3.0, "LMT_buffer", "Centre commenced release of stocks from 3 lakh t onion buffer", "https://www.newsonair.gov.in/tag/centre-commenced-release-of-stocks-from-onion-buffer-of-three-lakh-metric-tonnes", T),
 ("2023-08-20", "", ON, "buffer_procurement", 5.0, "LMT_target", "Buffer target raised 3 -> 5 lakh t; NCCF/NAFED to buy 1 lakh t each; retail sale at Rs 25/kg from 21-08-2023", PIB + "1950595", T),
 ("2023-08-22", "", ON, "buffer_procurement", 2410, "rs_qtl", "Additional 2 lakh t to be bought at Rs 2,410/qtl in Maharashtra & MP; special centres in Nashik, Ahmednagar", "https://www.deccanherald.com/amp/story/business%2Feconomy%2Fcentre-to-buy-2-lakh-metric-tonnes-onion-at-rs-2410-per-quintal-says-fadnavis-2656039", T),
 ("2023-12-11", "", ON, "buffer_procurement", 7.0, "LMT_target", "NCCF/NAFED directed to procure 7 lakh t for 2023-24 buffer; 5.10 lakh t procured, 2.73 lakh t disposed by 11-12-2023", "https://pib.gov.in/PressReleasePage.aspx?PRID=1985229", T),
 ("2024-03-26", "", ON, "buffer_procurement", 5.0, "LMT_target", "5 lakh t rabi-2024 buffer procurement directly from pre-registered farmers (DBT); 6.4 LMT bought in 2023-24", PIB + "2016405", T),
 ("2024-09-05", "", ON, "buffer_release", 35, "rs_kg_retail", "Calibrated release of 4.7 lakh t rabi buffer; retail at Rs 35/kg via NCCF/NAFED vans", PIB + "2052168", T),
 ("2025-07-01", "2025-09-04", ON, "buffer_procurement", 3.0, "LMT", "3 lakh t onion procured for 2025-26 buffer (avg ~Rs 15/kg); procurement started late (July) - START DATE APPROX", PIB + "2163638&reg=3&lang=2 | https://www.freepressjournal.in/pune/nashik-centre-begins-early-onion-procurement-via-nafed-nccf-2-lakh-tonne-target-set", F),
 ("2025-09-04", "", ON, "buffer_release", 24, "rs_kg_retail", "Retail sale of buffer onion at Rs 24/kg in Delhi, Mumbai, Ahmedabad; calibrated release begins", PIB + "2163638&reg=3&lang=2", T),
 ("2026-04-08", "", ON, "buffer_procurement", 2.0, "LMT_target", "2 lakh t PSF target for 2026-27; early procurement from April announced in Nashik", "https://www.freepressjournal.in/pune/nashik-centre-begins-early-onion-procurement-via-nafed-nccf-2-lakh-tonne-target-set", T),
 ("2026-05-15", "2026-07-03", ON, "buffer_procurement", 1235, "rs_qtl", "NAFED/NCCF procurement begins 15-05-2026 at Rs 12.35/kg while APMC prices Rs 1,100-1,250/qtl", "https://www.tribuneindia.com/news/business/nafed-begins-onion-procurement-at-rs-12-35-per-kg/ | https://www.businesstoday.in/latest/economy/story/govt-starts-buffer-onion-releases-as-festive-demand-nears-551618-2026-08-26", T),
 ("2026-06-07", "", ON, "other", 1580, "rs_qtl", "Buffer procurement quality norms relaxed (size 35-70 mm vs 45-65 mm, blemish tolerance); NAFED/NCCF rate ~Rs 1,580/qtl; farmers demand Rs 3,000", "https://www.business-standard.com/industry/agriculture/as-centre-eases-onion-procurement-norms-farmers-seek-msp-of-3-000-quintal-126060700126_1.html", T),
 ("2026-07-04", "", ON, "buffer_procurement", 2125, "rs_qtl", "Buffer procurement price raised 13% from Rs 1,875 to Rs 2,125/qtl effective 04-07-2026", "https://www.tribuneindia.com/news/nccf/govt-raises-onion-procurement-price-by-13-to-rs-2125-quintal-to-ensure-better-returns-for-farmers", T),
 ("2026-08-26", "", ON, "buffer_release", 1.21, "LMT_buffer", "Calibrated release of 2026-27 buffer (1.21 LMT procured, CWC storage); retail Rs 35/kg; Kanda Express rake Nashik->Delhi", "https://www.businesstoday.in/latest/economy/story/govt-starts-buffer-onion-releases-as-festive-demand-nears-551618-2026-08-26 | https://theindianawaaz.com/centre-begins-targeted-release-of-onion-buffer-stocks-to-check-seasonal-price-rise/", T),
 # ---------------- ONION: Maharashtra subsidies ----------------
 ("2018-11-01", "2018-12-31", ON, "state_subsidy_rs_qtl", 200, "rs_qtl", "MH onion subsidy Rs 200/qtl (max 200 qtl/farmer) for APMC sales 01-11-2018..15-12-2018, extended to 31-12-2018 (Jan 2019); Rs 150 cr outlay; paid in 2019", "https://www.newsclick.in/anticipating-electoral-loss-maharashtra-govt-increases-subsidy-deadline-onion-farmers | https://www.business-standard.com/article/economy-policy/onion-prices-in-maharashtra-hovering-at-2-year-lows-farmers-seek-govt-help-119020501178_1.html", T),
 ("2023-03-13", "", ON, "other", 300, "rs_qtl", "MH CM announces Rs 300/qtl ex-gratia for onion growers in Assembly (raised to 350 on 17-03-2023)", "https://www.deccanherald.com/india/maharashtra-government-announces-rs-300-per-quintal-ex-gratia-for-onion-farmers-1199772.html", T),
 ("2023-02-01", "2023-03-31", ON, "state_subsidy_rs_qtl", 350, "rs_qtl", "MH onion subsidy Rs 350/qtl (cap 200 qtl) on sales to APMCs/private markets/NAFED 01-02..31-03-2023; announced 17-03-2023; pending claims Rs 28.32 cr sanctioned Aug 2025", "https://theprint.in/india/farmers-march-maha-cm-says-onion-growers-to-get-rs-350-a-quintal-panel-to-monitor-forest-land-claims/1451981/ | https://www.freepressjournal.in/mumbai/maharashtra-news-onion-farmers-to-take-sigh-of-relief-as-government-sanctions-subsidy-for-350-per-quintal", T),
 ("2026-01-01", "", ON, "state_subsidy_rs_qtl", "", "rs_qtl", "NO 2026 Maharashtra onion subsidy found as of 2026-10-02: farmers demanded Rs 10,000 cr package (May-Jun 2026) and Rs 3,000/qtl floor; no GR located. Placeholder - verify with MH Marketing Dept GRs", "https://www.thehitavada.com/Encyc/2026/6/1/mah-onion-farmers-seek-rs-10k-cr-package-stable-export-policy-from-centre.html", F),
 # ---------------- ONION: Nashik APMC closures ----------------
 ("2023-08-21", "2023-08-23", ON, "apmc_strike_closure", 3, "days", "Nashik/Lasalgaon auctions halted ~3 days protesting 40% export duty; Lasalgaon resumed 24-08-2023", "https://www.newsonair.gov.in/tag/agriculture-produce-market-committees-of-lasalgaon-in-nashik-to-resume-auctions-of-onions/", T),
 ("2023-09-20", "2023-10-02", ON, "apmc_strike_closure", 13, "days", "Indefinite traders' strike in all 17 Nashik district APMCs vs export duty; resumed 03-10-2023 (Nandgaon stayed shut)", "https://www.newsonair.gov.in/onion-traders-to-stop-onion-auctions-in-nashik-district-of-maharashtra | https://www.deccanherald.com/amp/story/india%2Fmaharashtra%2Fonion-auctions-resume-at-apmcs-in-nashik-after-traders-call-off-strike-2710359", T),
 ("2024-04-04", "2024-04-17", ON, "apmc_strike_closure", 14, "days", "Auctions suspended at 15 Nashik APMCs over mathadi/weighing-charge levy dispute; partial resumption ~18-04 (Lasalgaon, Vinchur, Niphad, Nampur, Nashik), Pimpalgaon 22-04-2024", "https://www.freshplaza.com/asia/article/9619505/onion-auction-recommenced-at-5-of-15-apmcs-in-nashik-district/ | https://www.freshplaza.com/asia/article/9617458/onion-auction-resumes-in-nashik-india-after-14-days/", T),
 # ---------------- TOMATO ----------------
 ("2023-07-12", "", "Tomato", "buffer_procurement", "", "", "NAFED/NCCF directed to procure tomatoes from mandis in AP, Karnataka and Maharashtra (Satara, Narayangaon, Nashik supply) for consumption centres", PIB + "1938858", T),
 ("2023-07-14", "", "Tomato", "buffer_release", 90, "rs_kg_retail", "Subsidised retail of PSF tomatoes in Delhi-NCR from 14-07-2023 at Rs 90/kg, cut to 80 (16-07) and 70 (20-07)", PIB + "1940746", T),
 # ---------------- WHEAT ----------------
 ("2022-05-13", "2026-08-23", WH, "export_ban", 1, "flag", "Wheat export prohibited (DGFT 06/2015-20 dt 13-05-2022); G2G exceptions; made Free by DGFT 35/2026-27 dt 24-08-2026", "https://www.businesstoday.in/latest/story/govt-prohibits-wheat-exports-with-immediate-effect-to-manage-food-supply-333576-2022-05-14 | " + DG + "464a6838-3987-4369-bd8a-3a810216bfbe/Scan%20wheat%20english.pdf", T),
 ("2022-10-14", "2026-08-23", WH, "export_ban", 1, "flag", "Wheat flour/atta/maida/sooji (HS 1101) export prohibited under DGFT 39/2015-20 dt 14-10-2022 (cited in DGFT 55/2025-26); made Free by DGFT 34/2026-27 dt 24-08-2026", DG + "b9ac89ac-e740-4933-8b0c-3547bb310b0f/Notification%2055.pdf | " + DG + "7c58d938-9b88-42e7-9f4c-180e66228e16/Scan%20wheat%20flour%20english.pdf", T),
 ("2023-02-21", "", WH, "buffer_release", 50, "LMT_OMSS", "OMSS(D) 2023: total 50 LMT FCI wheat to be offloaded (additional 20 LMT) with reduced reserve price", PIB + "1901065", T),
 ("2023-06-28", "2024-03-31", WH, "buffer_release", 2150, "rs_qtl_reserve", "OMSS(D) weekly e-auctions start 28-06-2023; reserve Rs 2,150/qtl FAQ, Rs 2,125 URS (15 LMT initially)", "https://pib.gov.in/PressReleaseIframePage.aspx?PRID=1939046", T),
 ("2023-06-12", "2023-09-13", WH, "stock_limit", 3000, "MT_wholesaler", "Wheat stock limit order till 31-03-2024: traders/wholesalers 3000 MT, retailers 10 MT/outlet, processors 75% capacity", PIB + "1931805", T),
 ("2023-09-14", "2023-12-07", WH, "stock_limit", 2000, "MT_wholesaler", "Limit cut 3000 -> 2000 MT for traders/wholesalers & big chain retailers", "https://newsonair.gov.in/tag/and-big-chain-retailers", T),
 ("2023-12-08", "2024-02-07", WH, "stock_limit", 1000, "MT_wholesaler", "Limit cut 2000 -> 1000 MT; retailers 5 MT", PIB + "1983947", T),
 ("2024-02-08", "2024-03-31", WH, "stock_limit", 500, "MT_wholesaler", "Limit cut 1000 -> 500 MT till 31-03-2024", PIB + "2003950", T),
 ("2024-06-24", "2024-09-08", WH, "stock_limit", 3000, "MT_wholesaler", "New stock limit order till 31-03-2025: traders 3000 MT, retailers 10 MT/outlet", PIB + "2028225", T),
 ("2024-09-09", "2024-12-10", WH, "stock_limit", 2000, "MT_wholesaler", "Limit revised 3000 -> 2000 MT", PIB + "2054657", T),
 ("2024-11-28", "2025-03-31", WH, "buffer_release", 2325, "rs_qtl_reserve", "OMSS(D) 2024: FCI to offload 25 LMT wheat via e-auction, reserve Rs 2,325/qtl FAQ", PIB + "2078627", T),
 ("2024-12-11", "2025-02-19", WH, "stock_limit", 1000, "MT_wholesaler", "Limit revised 2000 -> 1000 MT", PIB + "2083178", T),
 ("2025-02-20", "2025-03-31", WH, "stock_limit", 250, "MT_wholesaler", "Limit revised to 250 MT traders, 4 MT/retail outlet", PIB + "2105124 | https://www.business-standard.com/industry/news/centre-further-tightens-wheat-stock-limit-for-wholesalers-retailers-processors-125082601069_1.html", T),
 ("2025-05-27", "2025-08-25", WH, "stock_limit", 3000, "MT_wholesaler", "New order till 31-03-2026: traders 3000 MT, retailers 10 MT/outlet", PIB + "2132343", T),
 ("2025-08-26", "2026-02-04", WH, "stock_limit", 2000, "MT_wholesaler", "Limit cut to 2000 MT, retailers 8 MT; order withdrawn 05-02-2026", "https://www.business-standard.com/industry/news/centre-further-tightens-wheat-stock-limit-for-wholesalers-retailers-processors-125082601069_1.html", T),
 ("2026-02-05", "", WH, "stock_limit", 0, "MT_wholesaler", "Wheat stock limit order of 27-05-2025 withdrawn (private stocks ~81 LMT); weekly stock declaration continues", PIB + "2224021", T),
 ("2026-01-16", "", WH, "other", 5, "LMT_export_quota", "Wheat flour (HS 1101) remains Prohibited but 5 LMT export permitted under DGFT authorisation (DGFT 55/2025-26)", DG + "b9ac89ac-e740-4933-8b0c-3547bb310b0f/Notification%2055.pdf", T),
 ("2026-02-24", "", WH, "other", 25, "LMT_export_quota", "Wheat remains Prohibited but 25 LMT export permitted (DGFT 62/2025-26); additional 5 LMT flour (DGFT 61/2025-26)", DG + "71b7c0b9-9d3d-4387-b2ff-1c5214cd4a08/Notification%2062.pdf | " + DG + "fec0005f-2b47-4880-af82-1b9a697ef82c/Notification%2061.pdf", T),
 ("2026-04-27", "", WH, "other", 25, "LMT_export_quota", "Additional 25 LMT wheat export permitted (total 50 LMT) (DGFT 13/2026-27)", DG + "0385952f-b63a-4b79-b39e-f332ac1c94ab/Noti%2013.pdf", T),
 ("2026-08-24", "", WH, "export_ban", 0, "flag", "Wheat (HS 10011900, 10019910) and wheat flour (HS 1101) export policy revised Prohibited -> Free (DGFT 35 & 34/2026-27)", DG + "464a6838-3987-4369-bd8a-3a810216bfbe/Scan%20wheat%20english.pdf | " + DG + "7c58d938-9b88-42e7-9f4c-180e66228e16/Scan%20wheat%20flour%20english.pdf", T),
 # ---------------- RICE ----------------
 ("2022-09-08", "2023-07-19", RI, "export_duty_pct", 20, "pct", "20% export duty on non-basmati white rice (replaced by ban 20-07-2023)", "https://www.business-standard.com/india-news/govt-prohibits-export-of-non-basmati-white-rice-says-dgft-notification-123072000768_1.html", T),
 ("2023-07-20", "2024-09-27", RI, "export_ban", 1, "flag", "Non-basmati white rice export prohibited (DGFT 20/2023); made Free subject to MEP USD 490/t on 28-09-2024 (DGFT 31/2024-25)", "https://www.business-standard.com/india-news/govt-prohibits-export-of-non-basmati-white-rice-says-dgft-notification-123072000768_1.html | " + DG + "b6cecc3e-1c54-4e85-a542-3040ed937630/Notificantion%20No.%2031%20-Eng.pdf", T),
 ("2023-08-25", "2023-10-16", RI, "export_duty_pct", 20, "pct", "20% export duty on parboiled non-basmati rice till 16-10-2023 (later extensions not captured)", "https://www.tribuneindia.com/news/business/government-imposes-20-per-cent-export-duty-on-parboiled-rice-538531", T),
 ("2024-09-28", "2024-10-22", RI, "min_export_price_usd_t", 490, "usd_per_t", "NBWR export Free subject to MEP USD 490/t; MEP lifted 23-10-2024 (DGFT 37/2024-25)", DG + "b6cecc3e-1c54-4e85-a542-3040ed937630/Notificantion%20No.%2031%20-Eng.pdf | " + DG + "28145972-b272-44ac-8778-c52502d4c5bd/Notification%20No.%2037-2024-25%20dated%2023.10.2024%20-English.pdf", T),
 ("2025-03-07", "", RI, "export_ban", 0, "flag", "Broken rice (HS 10064000) export policy Prohibited -> Free (DGFT 61/2024-25)", DG + "9fcbf4f3-cdbc-460b-a63d-2c10a01d50f1/Notification%2061%20dated%2007.03.2025%20-English.pdf", T),
 # ---------------- SUGAR ----------------
 ("2022-06-01", "2023-10-31", SU, "other", 100, "LMT_export_cap", "Sugar exports moved to 'Restricted' (permission of Directorate of Sugar) from 01-06-2022 (~100 LMT cap 2021-22); extended to 31-10-2023", "https://www.businesstoday.in/latest/economy/story/govt-imposes-restrictions-on-sugar-exports-from-june-1-334957-2022-05-25 | https://www.chinimandi.com/dgft-extends-sugar-export-restriction-till-31st-october-2023/", T),
 ("2023-10-18", "", SU, "other", "", "", "Restriction on sugar exports extended beyond 31-10-2023 till further orders (DGFT 36/2023)", DG + "610fb252-8583-49db-91af-d30c7b7d988f/DGFT%20Notification%20No.%2036-2023%20dated%2018.10.2023-English.pdf", T),
 ("2025-01-20", "2025-09-30", SU, "other", 10, "LMT_export_quota", "10 LMT sugar export quota for 2024-25 season (exports ~7.75 LMT)", "https://knnindia.co.in/news/newsdetails/sectors/india-exports-775-lakh-tonnes-of-sugar-in-202425-trade-body-urges-early-quota-for-next-season", T),
 ("2025-11-10", "2026-05-12", SU, "other", 15, "LMT_export_quota", "15 LMT sugar export allowed for 2025-26 season", "https://www.deccanherald.com/business/india-to-allow-15-lakh-tonnes-of-sugar-export-in-2025-26-season-3793473", T),
 ("2026-05-13", "2026-09-30", SU, "export_ban", 1, "flag", "Sugar exports Restricted -> Prohibited till 30-09-2026 (EU/US CXL/TRQ & AAS exempt); reverts to Restricted if not extended (DGFT 16/2026-27)", DG + "39108932-5da7-4496-b3a6-d8d9c1c0865b/sugar%20notification.pdf", T),
 ("2026-08-20", "", SU, "import_duty_pct", 0, "pct", "Raw sugar import policy amended; one-time AAS->TRQ conversion (DGFT 31/2026-27); ~1 MT duty-free raw sugar imports allowed; 3.5 LT export-bound sugar diverted to domestic market (26-08)", "https://www.businesstoday.in/latest/economy/story/india-to-divert-3-5-lakh-tonnes-of-export-sugar-to-local-market-as-prices-surge-551581-2026-08-26", T),
 ("2026-10-15", "2026-11-30", SU, "stock_limit", 1000, "qtl_dealer", "Sugar dealers: holding period cut 30 -> 15 days and limit 1,000 qtl (2,000 qtl Kolkata/Assam)", "https://www.chinimandi.com/sugar-stock-holding-period-cut-to-15-days-limit-set-at-1000-quintals/", T),
 # ---------------- EDIBLE OIL -> SOYABEAN ----------------
 ("2024-09-14", "2025-05-30", SO, "import_duty_pct", 20, "pct_BCD_crude_soy_oil", "BCD on crude soy/palm/sunflower oil 0 -> 20% (effective 27.5%); refined 12.5 -> 32.5% (eff. 35.75%)", PIB + "2055643", T),
 ("2025-05-31", "2026-09-23", SO, "import_duty_pct", 10, "pct_BCD_crude_soy_oil", "BCD on crude soy/palm/sunflower oil cut 20 -> 10% (effective 16.5%), notified 30-05-2025", "https://www.business-standard.com/markets/commodities/india-slashes-import-duty-on-crude-edible-oils-to-curb-rising-food-prices-125053001844_1.html", T),
 ("2026-09-24", "", SO, "import_duty_pct", 5, "pct_BCD_crude_soy_oil", "BCD crude soy & palm oil 10 -> 5% (eff. 11%); refined 32.5 -> 27.5%; crude sunflower 10 -> 0", "https://thenewsmill.com/2026/09/india-cuts-customs-duty-on-crude-and-refined-edible-oils-from-sept-24/ | https://theindianeye.com/2026/09/25/india-reduces-import-duty-on-edible-oils/", T),
 # ---------------- PULSES: stock limits ----------------
 *[("2021-07-02", "2021-10-31", c, "stock_limit", 200, "MT_wholesaler", "Pulses stock limit (all except moong) till 31-10-2021: wholesalers 200 MT (max 100 MT one variety), retailers 5 MT; relaxed 19-07-2021 to tur/masur/urad/chana only, importers exempt", PIB + "1732340 | " + PIB + "1736851", T) for c in (TUR, GRAM, URAD, MASUR)],
 *[("2023-06-02", "2023-09-24", c, "stock_limit", 200, "MT_wholesaler", "Tur & urad stock limit till 31-10-2023: wholesalers 200 MT, retailers 5 MT", PIB + "1929525", T) for c in (TUR, URAD)],
 *[("2023-09-25", "2023-12-31", c, "stock_limit", 50, "MT_wholesaler", "Tur & urad limit cut to 50 MT wholesalers, extended to 31-12-2023", PIB + "1960479", T) for c in (TUR, URAD)],
 *[("2024-06-21", "2024-09-30", c, "stock_limit", 200, "MT_wholesaler", "Tur & chana (incl. kabuli) stock limit till 30-09-2024: wholesalers 200 MT, retailers 5 MT; importers max 45 days", PIB + "2027694", T) for c in (TUR, GRAM)],
 # ---------------- PULSES: import policy ----------------
 ("2024-05-04", "2025-03-31", GRAM, "import_duty_pct", 0, "pct", "Duty-free import of desi chana till 31-03-2025; yellow-peas duty-free window extended (B/L by 31-10-2024)", "https://www.deccanherald.com/amp/story/india%2Fgovt-imposes-40-export-duty-on-onion-effective-may-4-3007182", T),
 ("2025-04-01", "", GRAM, "import_duty_pct", 10, "pct", "10% import duty on bengal gram (chana) from 01-04-2025 (Finance Ministry notif dt 27-03-2025)", "https://www.deccanherald.com/business/government-levies-10-import-duty-on-chickpea-from-april-1-3467048", T),
 ("2025-11-01", "", GRAM, "import_duty_pct", 30, "pct", "30% import duty (10% BCD + 20% AIDC) on yellow peas (substitute for chana/besan) for B/L on/after 01-11-2025", "https://www.khaleejtimes.com/world/asia/india-impose-import-duty-yellow-peas-november", T),
 ("2025-01-20", "2026-03-31", TUR, "other", "", "", "Tur import kept 'Free' till 31-03-2026 (DGFT 51/2024-25)", DG + "40f8b7be-48e6-400b-a0a5-4fca41680e63/Notfication%2051%20Eng.pdf", F),
 ("2026-03-31", "2027-03-31", TUR, "other", "", "", "Tur import kept 'Free' till 31-03-2027 (DGFT 72/2025-26); urad likewise (DGFT 71/2025-26)", DG + "9d8dcdc3-7485-4438-bfe4-521720c2bbe4/Noti-72-Tur.pdf", T),
 # ---------------- MSP/PSS procurement windows in Maharashtra ----------------
 ("2024-10-15", "2025-02-06", SO, "procurement_window", 14.13, "LMT_approved_MH", "Soybean PSS in MH at MSP Rs 4,892: 90 days from 15-10-2024, extended to 31-01-2025 then to 06-02-2025; NAFED 8.35 + NCCF 2.84 LMT bought in MH", "https://www.indiancooperative.com/co-op-news-snippets/nafed-nccf-procure-over-11-lakh-mt-of-soybean-mos/ | https://www.business-standard.com/industry/agriculture/centre-extends-soybean-procurement-deadline-in-maharashtra-raj-to-jan-31-125011300909_1.html", T),
 ("2025-11-15", "2026-02-12", SO, "procurement_window", 18.507, "LMT_approved_MH", "Soybean PSS 2025-26 in MH at MSP Rs 5,328: registration from 30-10-2025, purchase 15-11-2025 to 12-02-2026 (90 days); >11 LMT procured", "https://www.businessworld.in/article/soybean-procurement-completed-on-schedule-maharashtra-minister-598368 | https://www.newsonair.gov.in/union-minister-shivraj-singh-chouhan-clears-%e2%82%b915000-crore-kharif-procurement-plan", T),
 ("2025-11-15", "2026-02-12", URAD, "procurement_window", 3.2568, "LMT_approved_MH", "Urad PSS 2025-26 MH approval 3,25,680 t; MH kharif pulses/oilseed purchase from 15-11-2025 for 90 days (end date assumed = soybean)", "https://www.newsonair.gov.in/union-minister-shivraj-singh-chouhan-clears-%e2%82%b915000-crore-kharif-procurement-plan | https://www.igrain.in/posts/maharashtra-to-start-kharif-pulses-and-oilseeds-procurement", F),
 ("2025-11-15", "2026-02-12", MOONG, "procurement_window", 0.33, "LMT_approved_MH", "Moong PSS 2025-26 MH approval 33,000 t; purchase from 15-11-2025 for 90 days (end date assumed)", "https://www.newsonair.gov.in/union-minister-shivraj-singh-chouhan-clears-%e2%82%b915000-crore-kharif-procurement-plan | https://www.igrain.in/posts/maharashtra-to-start-kharif-pulses-and-oilseeds-procurement", F),
 ("2025-02-17", "", TUR, "procurement_window", "", "", "Tur PSS kharif 2024-25 approved in 9 states incl. MH; 100% of state production to be bought for 4 years (Budget 2025); MH window dates not captured", PIB + "2104121", F),
 ("2026-01-27", "", TUR, "procurement_window", 3.37, "LMT_approved_MH", "Centre approves PSS procurement of 3.37 LMT tur from Maharashtra (Rs 2,696 cr) at MSP Rs 8,000; window dates not captured", "https://www.global-agriculture.com/india-region/centre-clears-tur-procurement-in-maharashtra-%E2%82%B92696-crore-msp-outlay/", F),
 ("2026-03-01", "", GRAM, "procurement_window", 7.61, "LMT_target_MH", "Chana PSS MH 2026: registration 01-03..31-03-2026, target 7.61 LMT at MSP Rs 5,875; purchase start date not announced at time of report", "https://www.igrain.in/posts/chana-gram-procurement-in-maharashtra-under-msp", F),
 # ---------------- COTTON ----------------
 ("2025-08-19", "2025-12-31", "Cotton", "import_duty_pct", 0, "pct", "11% import duty on raw cotton (HS 5201) waived 19-08 to 30-09-2025, extended to 31-12-2025", "https://www.newsonair.gov.in/govt-extends-import-duty-exemption-on-raw-cotton-until-31st-december-2025", T),
 # ---------------- STATE-WIDE ----------------
 ("2026-09-26", "", "ALL", "other", 265, "talukas", "MH declares Trigger-1 drought in 265 of 358 talukas (kharif 2026): land-revenue concession, crop-loan restructuring, stay on farm-loan recovery, pump power-bill concession", "https://thelivenagpur.com/2026/09/26/maharashtra-brings-265-talukas-under-trigger-1-drought-measures-relief-measures-announced/", T),
]

# ---------------- MSP ----------------
KH = ["Paddy (Dhan)(Common)", "Jowar (Sorghum)", "Bajra (Pearl Millet/Cumbu)", "Maize", TUR, MOONG, URAD, "Groundnut", SO, "Cotton"]
KHARIF = {  # marketing_year: (announced, url, values in KH order)
 "2019-20": ("2019-07-03", PIB + "1576844", [1815, 2550, 2000, 1760, 5800, 7050, 5700, 5090, 3710, 5255]),
 "2020-21": ("2020-06-01", PIB + "1628348", [1868, 2620, 2150, 1850, 6000, 7196, 6000, 5275, 3880, 5515]),
 "2021-22": ("2021-06-09", PIB + "1725612", [1940, 2738, 2250, 1870, 6300, 7275, 6300, 5550, 3950, 5726]),
 "2022-23": ("2022-06-08", PIB + "1832172", [2040, 2970, 2350, 1962, 6600, 7755, 6600, 5850, 4300, 6080]),
 "2023-24": ("2023-06-07", PIB + "1930443&reg=48&lang=2", [2183, 3180, 2500, 2090, 7000, 8558, 6950, 6377, 4600, 6620]),
 "2024-25": ("2024-06-19", PIB + "2026698", [2300, 3371, 2625, 2225, 7550, 8682, 7400, 6783, 4892, 7121]),
 "2025-26": ("2025-05-28", PIB + "2131983&reg=48&lang=2", [2369, 3699, 2775, 2400, 8000, 8768, 7800, 7263, 5328, 7710]),
 "2026-27": ("2026-05-13", PIB + "2260617&reg=3&lang=1", [2441, 4023, 2900, 2410, 8450, 8780, 8200, 7517, 5708, 8267]),
}
RB = [WH, GRAM, MASUR, "Mustard", "Safflower"]
RABI = {
 "2019-20": ("2018-10-03", PIB + "1548396&reg=48&lang=2", [1840, 4620, 4475, 4200, 4945]),
 "2020-21": ("2019-10-23", "https://www.pib.gov.in/newsite/PrintRelease.aspx?relid=193961&reg=48&lang=2", [1925, 4875, 4800, 4425, 5215]),
 "2021-22": ("2020-09-21", PIB + "1657426", [1975, 5100, 5100, 4650, 5327]),
 "2022-23": ("2021-09-08", PIB + "1753109", [2015, 5230, 5500, 5050, 5441]),
 "2023-24": ("2022-10-18", PIB + "1868761", [2125, 5335, 6000, 5450, 5650]),
 "2024-25": ("2023-10-18", PIB + "1968729", [2275, 5440, 6425, 5650, 5800]),
 "2025-26": ("2024-10-16", PIB + "2065310&reg=48&lang=2", [2425, 5650, 6700, 5950, 5940]),
 "2026-27": ("2025-10-01", PIB + "2173567", [2585, 5875, 7000, 6200, 6540]),
 "2027-28": ("2026-09-30", "https://www.business-standard.com/amp/economy/news/cabinet-rabi-msp-2027-28-wheat-safflower-mustard-126093000756_1.html", [2610, 5958, 7390, 6613, 7215]),
}
M = [("kharif", my, c, v, d, u, T) for my, (d, u, vals) in KHARIF.items() for c, v in zip(KH, vals)]
M += [("rabi", my, c, v, d, u, T) for my, (d, u, vals) in RABI.items() for c, v in zip(RB, vals)]

# ---------------- SCHEMES ----------------
S = [
 ("Shetmal Taran Karj Yojana (MSAMB pledge loan)", "Tur, moong, urad, soybean, sunflower, chana, paddy, safflower, jowar, bajra, maize, wheat, turmeric, rajma, cashew, raisins, areca (NOT onion)",
  "Loan up to 75% of value (valued at lower of market price or MSP) for 180 days at 6%; then 8% for next 6 months and 12% thereafter; storage, supervision and insurance by APMC free; also against MSWC/CWC warehouse receipts",
  "Producer farmers only (traders' produce not accepted)", "Deposit produce in participating APMC godown and apply at the APMC (circular & form on MSAMB site)", "Running since 1990-91",
  "https://www.msamb.com/schemes/pledgefinance", T),
 ("e-NWR pledge finance + Credit Guarantee Scheme (CGS-NPF)", "Any notified agri/horti produce stored in WDRA-registered warehouses",
  "Rs 1,000 cr guarantee corpus so banks lend against electronic negotiable warehouse receipts; lets farmer hold stock instead of distress sale",
  "Farmers (incl. small/marginal), FPOs, cooperatives, MSMEs, traders using WDRA-registered warehouses", "Deposit in WDRA-registered warehouse, obtain e-NWR, apply for pledge loan at scheduled/cooperative bank", "Launched 16-12-2024",
  PIB + "2085018", T),
 ("Post-harvest interest subvention on loans against NWR (MISS/KCC)", "All crops stored in WDRA-accredited warehouses",
  "Concessional 7% p.a. (effective 4% with prompt repayment on crop loans) extended up to 6 months post-harvest against negotiable warehouse receipts; MISS limit raised Rs 3 -> 5 lakh in Budget 2025",
  "Small & marginal farmers holding Kisan Credit Card", "Through KCC-issuing bank against NWR", "Ongoing (scheme continued 2025-26)",
  PIB + "1559071 | " + PIB + "2099696", T),
 ("PM-AASHA: Price Support Scheme (PSS) at MSP", "Pulses (tur, urad, masur up to 100% of state output through 2028-29; others 25%), oilseeds (soybean etc.), copra",
  "Central agencies NAFED/NCCF buy FAQ produce at MSP from pre-registered farmers; payment by DBT",
  "Pre-registered farmers with FAQ produce in notified procurement window", "Register on NAFED e-Samridhi / NCCF e-Samyukti or MH state agency centres when window opens (MH soybean 2025-26: reg. from 30-10-2025, purchase 15-11-2025..12-02-2026)", "Continued for 15th FC cycle to 2025-26; 100% tur/urad/masur for 4 years from 2025",
  PIB + "2104121 | " + PIB + "2155528", T),
 ("Price Deficit Payment Scheme / Bhavantar (Madhya Pradesh only - NOT available in Maharashtra)", "Soybean (MP)",
  "Pays difference between MSP and state model rate to registered MP farmers who sell in MP mandis",
  "MP farmers registered on e-Uparjan (2025: 03-10..24-10-2025; 2026: 03-10..17-10-2026)", "MP e-Uparjan portal/CSC/PACS - not applicable to Maharashtra farmers", "Kharif 2025 and 2026 (MP)",
  "https://indianmasterminds.com/news/mp-bhavantar-yojana-soybean-farmers-registration-148771/ | https://www.socialnews.xyz/2026/09/30/mp-soybean-registration-under-bhavantar-yojana-to-begin-on-oct-3/", T),
 ("MSWC warehousing concession + warehouse-receipt pledge", "Foodgrains, pulses, oilseeds, cotton etc.",
  "Rebate up to 50% on storage charges for farmers (also SC/ST & tribal-area farmers); 25% of space reserved for farmers; NWR usable for bank pledge loans",
  "Producer farmers", "Deposit at nearest MSWC warehouse centre; take receipt to bank for pledge loan", "Ongoing",
  "https://mswarehousing.com/MSwhs/about-us/ | https://mswarehousing.com/MSwhs/pledge-loan/", T),
 ("Maharashtra onion price subsidy (ad hoc)", "Onion",
  "Past rounds: Rs 200/qtl (sales 01-11..31-12-2018, max 200 qtl) and Rs 350/qtl (sales 01-02..31-03-2023, max 200 qtl). No 2026 round found as of 2026-10-02",
  "Onion growers with 7/12 crop record and APMC/private market/NAFED sale receipts in the notified window", "Apply via APMC with sale patti, 7/12 and bank details when GR is issued", "Ad hoc (2018-19, 2023)",
  "https://www.freepressjournal.in/mumbai/maharashtra-news-onion-farmers-to-take-sigh-of-relief-as-government-sanctions-subsidy-for-350-per-quintal | https://www.newsclick.in/anticipating-electoral-loss-maharashtra-govt-increases-subsidy-deadline-onion-farmers", T),
 ("PM-KISAN (income support - context only)", "All", "Rs 6,000/year in three Rs 2,000 instalments by DBT (23rd instalment 20-06-2026); not linked to sale timing",
  "Eligible landholding farmer families (Aadhaar-seeded bank account)", "Register via pmkisan.gov.in / CSC", "Ongoing", PIB + "2275744&reg=3&lang=1", T),
 ("Maharashtra drought relief - Trigger-1 (kharif 2026)", "All (265 talukas)",
  "Land-revenue concession, crop-loan restructuring, stay on recovery of agri loans, pump power-bill concession, no disconnection - reduces cash pressure to sell immediately after harvest",
  "Farmers in the 265 notified talukas", "Automatic via district administration/banks; panchnamas by collectors", "Declared 26-09-2026",
  "https://thelivenagpur.com/2026/09/26/maharashtra-brings-265-talukas-under-trigger-1-drought-measures-relief-measures-announced/", T),
 ("e-NAM (National Agriculture Market)", "All traded commodities in integrated mandis",
  "Online bidding across a larger buyer pool, sale proceeds direct to bank; 1,656 mandis, 1.80 cr farmers registered (Feb 2026)",
  "Any farmer selling in an e-NAM-integrated APMC", "Register on enam.gov.in / mobile app or at the APMC gate", "Ongoing", PIB + "2241414&reg=3&lang=2", T),
 ("Kisan Rath app", "All farm produce", "Find trucks/transport aggregators for primary & secondary movement of produce to better markets",
  "Farmers, FPOs, traders", "Download Kisan Rath app (NIC)", "Launched 17-04-2020", PIB + "1615352", T),
]


def write(name, header, rows):
    with (OUT / name).open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(name, len(rows), "rows,", sum(r[-1] == T for r in rows), "verified")


if __name__ == "__main__":
    for r in E:
        assert len(r) == 9 and r[-1] in (T, F) and r[0] <= (r[1] or "9999"), r
    E.sort(key=lambda r: (r[0], r[2]))
    write("events.csv", "date_start,date_end,commodity,event_type,value,unit,description,source_url,verified".split(","), E)
    write("msp.csv", "season,marketing_year,commodity,msp_rs_qtl,announced_date,source_url,verified".split(","), M)
    write("schemes.csv", "scheme,crops,benefit,eligibility,how_to_apply,period,source_url,verified".split(","), S)
