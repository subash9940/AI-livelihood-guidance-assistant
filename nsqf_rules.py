"""
NSQF Rules and Recommendation Engine for Nivara — AI Livelihood Guidance Assistant.
Matches beneficiary background, education, mobility constraints, and interests
against NSQF-aligned job roles and PM-AJAY skill training schemes.
"""
import re
from typing import Dict, Any, List, Tuple

# NSQF Eligible Trades Catalog with PM-AJAY Alignment & Concrete Skill Gaps
TRADES_CATALOG = {
    "food_processing": {
        "trade_name": "Food Processing & Agri-Value Addition Technician",
        "qp_name": "Pickle Making Technician",
        "qp_code": "FIC/Q0102",
        "nsqf_level": "NSQF Level 4",
        "ssc_name": "Food Industry Capacity & Skill Initiative (FICSI)",
        "trade_name_hi": "खाद्य प्रसंस्करण एवं कृषि मूल्य संवर्धन तकनीशियन",
        "trade_name_mr": "अन्न प्रक्रिया व कृषी मूल्यवर्धन तंत्रज्ञ",
        "trade_name_pa": "ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ ਅਤੇ ਖੇਤੀ ਮੁੱਲ ਵਾਧਾ ਤਕਨੀਸ਼ੀਅਨ",
        "min_education": ["none", "5th", "8th", "10th", "12th", "graduate"],
        "mobility_requirement": "low",  # Can be conducted in village/cluster
        "sector": "Food Industry Capacity & Skill Initiative (FICSI)",
        "duration_hours": "300 Hours (Approx. 2.5 Months)",
        "training_programme": "PM-AJAY Free Skill Training & Certification (Stipend Provided)",
        "training_centre": "Jan Shikshan Sansthan (JSS) & District PMKK Center",
        "local_opportunity": "Micro-Enterprise in local spice/pickle/bakery processing with PMEGP/Mudra Shishu Loan up to ₹50,000",
        "skill_gaps": [
            {
                "skill": "FSSAI Food Safety, Hygiene & Sanitation Standards",
                "where": "Jan Shikshan Sansthan (JSS) in-person practical lab"
            },
            {
                "skill": "Fruit & Vegetable Post-Harvest Preservation Techniques",
                "where": "PMKK District Training Center hands-on workshop"
            },
            {
                "skill": "Vacuum Packaging, Sealing & FSSAI Product Labeling",
                "where": "Skill India Digital (SID) self-paced certification course"
            },
            {
                "skill": "Micro-Enterprise Costing & PMEGP/Mudra Loan Application",
                "where": "Rural Self Employment Training Institute (RSETI) EDP module"
            }
        ],
        "steps_en": [
            "Enroll in PM-AJAY certified Food Processing Course (Free + ₹1,500 monthly stipend)",
            "Hands-on training at District Jan Shikshan Sansthan with practical food safety standards",
            "Receive Government-recognized NSQF Level 3 Certificate from FICSI",
            "Avail Mudra Shishu grant/loan for village-level processing unit or join farmer producer cluster"
        ],
        "steps_hi": [
            "पीएम-अजय निःशुल्क खाद्य प्रसंस्करण कोर्स में नामांकन (मुफ्त प्रशिक्षण + ₹1,500 मासिक वजीफा)",
            "जिला जन शिक्षण संस्थान में खाद्य सुरक्षा और पैकेजिंग का व्यावहारिक प्रशिक्षण",
            "FICSI द्वारा भारत सरकार मान्यता प्राप्त NSQF लेवल 3 प्रमाणपत्र प्राप्त करें",
            "मुद्रा शिशु लोन के साथ गाँव में अपनी यूनिट शुरू करें या स्थानीय क्लस्टर से जुड़ें"
        ],
        "steps_mr": [
            "पीएम-अजय मोफत अन्न प्रक्रिया अभ्यासक्रमात प्रवेश (विनामूल्य + ₹1,500 मासिक विद्यावेतन)",
            "जिल्हा जन शिक्षण संस्थान केंद्रात अन्न प्रक्रिया व पॅकेजिंगचे प्रात्यक्षिक प्रशिक्षण",
            "FICSI कडून शासनमान्य NSQF स्तर 3 प्रमाणपत्र मिळवा",
            "मुद्रा शिशु कर्जाद्वारे गावात स्वतःचे केंद्र सुरू करा किंवा शेतकरी गटामध्ये सहभागी व्हा"
        ],
        "steps_pa": [
            "ਪੀਐਮ-ਅਜੇ ਮੁਫ਼ਤ ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ ਕੋਰਸ ਵਿੱਚ ਦਾਖਲਾ (ਮੁਫ਼ਤ ਸਿਖਲਾਈ + ₹1,500 ਮਹੀਨਾਵਾਰ ਵਜ਼ੀਫ਼ਾ)",
            "ਜ਼ਿਲ੍ਹਾ ਜਨ ਸ਼ਿਕਸ਼ਨ ਸੰਸਥਾਨ ਵਿਖੇ ਫੂਡ ਪ੍ਰੋਸੈਸਿੰਗ ਦਾ ਅਮਲੀ ਅਭਿਆਸ",
            "FICSI ਵੱਲੋਂ ਸਰਕਾਰ ਦੁਆਰਾ ਮਾਨਤਾ ਪ੍ਰਾਪਤ NSQF ਲੈਵਲ 3 ਸਰਟੀਫਿਕੇਟ ਪ੍ਰਾਪਤ ਕਰੋ",
            "ਮੁਦਰਾ ਸ਼ਿਸ਼ੂ ਲੋਨ ਰਾਹੀਂ ਆਪਣੇ ਪਿੰਡ ਵਿੱਚ ਪ੍ਰੋਸੈਸਿੰਗ ਯੂਨਿਟ ਸ਼ੁਰੂ ਕਰੋ"
        ]
    },
    "apparel_tailoring": {
        "trade_name": "Self-Employed Tailor & Apparel Specialist",
        "qp_name": "Self Employed Tailor",
        "qp_code": "AMH/Q1947",
        "nsqf_level": "NSQF Level 4",
        "ssc_name": "Apparel, Made-Ups & Home Furnishing Sector Skill Council (AMHSSC)",
        "trade_name_hi": "स्व-रोजगार दर्जी एवं परिधान विशेषज्ञ",
        "trade_name_mr": "स्वयंरोजगार टेलर व वस्त्र निर्मिती तज्ज्ञ",
        "trade_name_pa": "ਸਵੈ-ਰੋਜ਼ਗਾਰ ਟੇਲਰ ਅਤੇ ਕੱਪੜਾ ਮਾਹਰ",
        "min_education": ["none", "5th", "8th", "10th", "12th", "graduate"],
        "mobility_requirement": "low",
        "sector": "Apparel, Made-Ups & Home Furnishing Sector Skill Council (AMHSSC)",
        "duration_hours": "340 Hours (Approx. 3 Months)",
        "training_programme": "PM-AJAY Special Beneficiary Tailoring & Garment Skill Initiative",
        "training_centre": "Rural Self Employment Training Institute (RSETI) & JSS Center",
        "local_opportunity": "Home-based boutique or contract manufacturing for local school uniforms and textile markets",
        "skill_gaps": [
            {
                "skill": "Commercial Garment Pattern Drafting & Cutting",
                "where": "District Jan Shikshan Sansthan (JSS) apparel lab"
            },
            {
                "skill": "High-Speed Industrial Sewing Machine Operation & Maintenance",
                "where": "PMKVY Accredited Apparel Training Hub"
            },
            {
                "skill": "Garment Quality Inspection, Finishing & Export Stitch Standards",
                "where": "Apparel, Made-Ups & Home Furnishing SSC certified workshop"
            },
            {
                "skill": "Direct Market Linkage & Tailoring Boutique Financial Management",
                "where": "SWAYAM portal / RSETI micro-enterprise development module"
            }
        ],
        "steps_en": [
            "Enroll in NSQF Level 3 Self-Employed Tailor training with free tool kit voucher",
            "Learn garment pattern drafting, computerized sewing, and finished cloth quality control",
            "Complete Sector Skill Council practical assessment and receive national certificate",
            "Receive sewing machine subsidy under PM-AJAY and set up village tailoring unit"
        ],
        "steps_hi": [
            "टूलकिट वाउचर के साथ NSQF लेवल 3 टेलर प्रशिक्षण में निःशुल्क प्रवेश लें",
            "सिलाई पैटर्न, आधुनिक सिलाई मशीन व फिनिशिंग का व्यावहारिक कौशल सीखें",
            "कौशल परिषद से राष्ट्रीय स्तर का प्रमाण पत्र प्राप्त करें",
            "पीएम-अजय सिलाई मशीन सब्सिडी सहायता लेकर घर/गाँव में दुकान शुरू करें"
        ],
        "steps_mr": [
            "साहित्य किटसह NSQF स्तर 3 टेलरिंग अभ्यासक्रमात विनामूल्य प्रवेश",
            "वस्त्र कटिंग, आधुनिक शिलाई यंत्र व दर्जा तपासणीचे प्रात्यक्षिक शिक्षण",
            "कौशल्य परिषदेचे राष्ट्रीय प्रमाणपत्र प्राप्त करा",
            "पीएम-अजय शिलाई मशीन अनुदानाचा लाभ घेऊन गावात शिवणकाम केंद्र सुरू करा"
        ],
        "steps_pa": [
            "ਟੂਲਕਿੱਟ ਵਾਊਚਰ ਨਾਲ NSQF ਲੈਵਲ 3 ਟੇਲਰਿੰਗ ਸਿਖਲਾਈ ਵਿੱਚ ਦਾਖਲਾ ਲਵੋ",
            "ਕੱਪੜੇ ਦੀ ਕਟਿੰਗ ਅਤੇ ਆਧੁਨਿਕ ਸਿਲਾਈ ਦਾ ਅਮਲੀ ਗਿਆਨ ਸਿੱਖੋ",
            "ਨੈਸ਼ਨਲ ਕੌਂਸਲ ਵੱਲੋਂ ਮਾਨਤਾ ਪ੍ਰਾਪਤ ਸਰਟੀਫਿਕੇਟ ਹਾਸਲ ਕਰੋ",
            "ਪੀਐਮ-ਅਜੇ ਸਿਲਾਈ ਮਸ਼ੀਨ ਸਬਸਿਡੀ ਨਾਲ ਆਪਣਾ ਕਾਰੋਬਾਰ ਸ਼ੁਰੂ ਕਰੋ"
        ]
    },
    "solar_technician": {
        "trade_name": "Solar PV Installer (Suryamitra)",
        "qp_name": "Solar PV Installer (Suryamitra)",
        "qp_code": "SGJ/Q0101",
        "nsqf_level": "NSQF Level 4",
        "ssc_name": "Skill Council for Green Jobs (SCGJ)",
        "trade_name_hi": "सोलर पीवी इंस्टॉलर (सूर्यमित्र)",
        "trade_name_mr": "सोलर पीव्ही इंस्टॉलर (सूर्यमित्र)",
        "trade_name_pa": "ਸੋਲਰ ਪੀਵੀ ਇੰਸਟਾਲਰ (ਸੂਰਿਆਮਿੱਤਰ)",
        "min_education": ["10th", "12th", "graduate", "iti"],
        "mobility_requirement": "medium",
        "sector": "Skill Council for Green Jobs (SCGJ)",
        "duration_hours": "300 Hours",
        "training_programme": "PM-AJAY Suryamitra Green Energy Skill Initiative",
        "training_centre": "Government Industrial Training Institute (ITI) / NISE Partner Center",
        "local_opportunity": "Rooftop solar installation under PM Surya Ghar Yojana and agricultural solar pump maintenance",
        "skill_gaps": [
            {
                "skill": "Photovoltaic (PV) Module Mounting & Rooftop Structural Alignment",
                "where": "Government Industrial Training Institute (ITI) Solar Lab"
            },
            {
                "skill": "High-Voltage Electrical Safety, DC Wiring & Earthing Protocols",
                "where": "National Institute of Solar Energy (NISE) certified center"
            },
            {
                "skill": "Grid-Tied Inverter Synchronization & Storage Battery Diagnostics",
                "where": "Skill Council for Green Jobs (SCGJ) training partner"
            },
            {
                "skill": "PM Surya Ghar Consumer Net-Metering & DISCOM Portal Onboarding",
                "where": "Skill India Digital (SID) e-learning module"
            }
        ],
        "steps_en": [
            "Join PM-AJAY sponsored Suryamitra Solar PV installation program (100% sponsored)",
            "Undergo rigorous electrical safety, solar panel wiring, and inverter installation training",
            "Clear Skill Council for Green Jobs (SCGJ) examination and secure Suryamitra ID badge",
            "Direct placement with DISCOM vendors or independent contractor for PM Surya Ghar installations"
        ],
        "steps_hi": [
            "पीएम-अजय प्रायोजित सूर्यमित्र सोलर इंस्टॉलेशन प्रोग्राम में 100% फ्री प्रवेश लें",
            "इलेक्ट्रिकल सुरक्षा, सोलर पैनल फिटिंग और इन्वर्टर वायरिंग का गहन प्रशिक्षण",
            "ग्रीन जॉब्स काउंसिल परीक्षा उत्तीर्ण कर आधिकारिक सूर्यमित्र पहचान पत्र पाएं",
            "पीएम सूर्य घर योजना व डिस्कॉम वेंडर्स के साथ सीधे रोजगार या ठेकेदारी से जुड़ें"
        ],
        "steps_mr": [
            "पीएम-अजय पुरस्कृत सूर्यमित्र सोलर अभ्यासक्रमात मोफत प्रवेश घ्या",
            "विद्युत सुरक्षा, सोलर पॅनेल फिटिंग आणि इन्व्हर्टर जोडणीचे सविस्तर प्रशिक्षण",
            "ग्रीन जॉब्स कौन्सिल परीक्षा उत्तीर्ण होऊन सूर्यमित्र ओळखपत्र मिळवा",
            "पीएम सूर्य घर योजना व स्थानिक कंत्राटदारांसोबत हमखास नोकरी किंवा व्यवसाय सुरू करा"
        ],
        "steps_pa": [
            "ਸੂਰਿਆਮਿੱਤਰ ਸੋਲਰ ਪੀਵੀ ਇੰਸਟਾਲੇਸ਼ਨ ਕੋਰਸ ਵਿੱਚ 100% ਮੁਫ਼ਤ ਦਾਖਲਾ ਲਵੋ",
            "ਇਲੈਕਟ੍ਰੀਕਲ ਸੁਰੱਖਿਆ ਅਤੇ ਸੋਲਰ ਪੈਨਲ ਫਿਟਿੰਗ ਦੀ ਤਕਨੀਕੀ ਸਿਖਲਾਈ",
            "ਗ੍ਰੀਨ ਜਾਬਸ ਕੌਂਸਲ ਪ੍ਰੀਖਿਆ ਪਾਸ ਕਰਕੇ ਅਧਿਕਾਰਤ ਸਰਟੀਫਿਕੇਟ ਲਵੋ",
            "ਪੀਐਮ ਸੂਰਿਆ ਘਰ ਯੋਜਨਾ ਤਹਿਤ ਰੋਜ਼ਗਾਰ ਪ੍ਰਾਪਤ ਕਰੋ"
        ]
    },
    "automotive_ev": {
        "trade_name": "Two-Wheeler & EV Service Technician",
        "qp_name": "Two Wheeler Service Technician",
        "qp_code": "ASC/Q1411",
        "nsqf_level": "NSQF Level 4",
        "ssc_name": "Automotive Skills Development Council (ASDC)",
        "trade_name_hi": "टू-व्हीलर एवं ईवी सर्विस तकनीशियन",
        "trade_name_mr": "दुचाकी व ईव्ही सर्व्हिस तंत्रज्ञ",
        "trade_name_pa": "ਟੂ-ਵ੍ਹੀਲਰ ਅਤੇ ਈਵੀ ਸਰਵਿਸ ਤਕਨੀਸ਼ੀਅਨ",
        "min_education": ["8th", "10th", "12th", "graduate"],
        "mobility_requirement": "medium",
        "sector": "Automotive Skills Development Council (ASDC)",
        "duration_hours": "350 Hours",
        "training_programme": "PM-AJAY Automotive & Electric Mobility Livelihood Track",
        "training_centre": "District Skill Center & Automotive Partner Workshop",
        "local_opportunity": "Employed at dealership service centers or opening a village two-wheeler EV battery swapping and repair point",
        "skill_gaps": [
            {
                "skill": "Two-Wheeler Multi-Brand Engine Diagnostics & Brake Calibration",
                "where": "District ITI / Automotive Skills Development Council (ASDC) Workshop"
            },
            {
                "skill": "Electric Vehicle (EV) Powertrain, BLDC Motor & Controller Servicing",
                "where": "PMKK Advanced Automotive Lab"
            },
            {
                "skill": "Lithium-Ion Battery Swapping, BMS Diagnostics & Thermal Safety",
                "where": "Tata STRIVE / ASDC specialized EV training module"
            },
            {
                "skill": "Independent Garage Management & Digital Job-Card Billing",
                "where": "RSETI Rural Entrepreneurship Center"
            }
        ],
        "steps_en": [
            "Enroll in Automotive & EV Maintenance course with hands-on toolkits",
            "Learn engine diagnostics, brake calibration, and electric vehicle battery systems",
            "Receive ASDC National Skill Qualification certification",
            "Get placed at authorized dealership or set up village repair service with Mudra loan"
        ],
        "steps_hi": [
            "टू-व्हीलर और ईवी मरम्मत कोर्स में टूलकिट सहायता के साथ प्रवेश लें",
            "इंजन डायग्नोस्टिक्स, ब्रेक सर्विस और इलेक्ट्रिक बैटरी सिस्टम सीखें",
            "ASDC राष्ट्रीय कौशल योग्यता प्रमाण पत्र हासिल करें",
            "अधिकृत वर्कशॉप में नौकरी पाएं या मुद्रा लोन से अपना सर्विस सेंटर खोलें"
        ],
        "steps_mr": [
            "दुचाकी व ईव्ही दुरुस्ती अभ्यासक्रमात साहित्यासह प्रवेश घ्या",
            "इंजिन तपासणी, ब्रेक सिस्टीम आणि इलेक्ट्रिक बॅटरीचे प्रगत प्रशिक्षण",
            "ASDC राष्ट्रीय कौशल्य प्रमाणपत्र मिळवा",
            "अधिकृत शोरूममध्ये नोकरी मिळवा किंवा मुद्रा कर्जातून स्वतःचे गॅरेज सुरू करा"
        ],
        "steps_pa": [
            "ਟੂ-ਵ੍ਹੀਲਰ ਅਤੇ ਈਵੀ ਸਰਵਿਸ ਕੋਰਸ ਵਿੱਚ ਦਾਖਲਾ ਲਵੋ",
            "ਇੰਜਣ ਅਤੇ ਬੈਟਰੀ ਸਿਸਟਮ ਦਾ ਅਮਲੀ ਕੰਮ ਸਿੱਖੋ",
            "ASDC ਸਰਟੀਫਿਕੇਟ ਪ੍ਰਾਪਤ ਕਰੋ",
            "ਵਰਕਸ਼ਾਪ ਵਿੱਚ ਨੌਕਰੀ ਕਰੋ ਜਾਂ ਆਪਣਾ ਸਰਵਿਸ ਸੈਂਟਰ ਸ਼ੁਰੂ ਕਰੋ"
        ]
    },
    "digital_csc": {
        "trade_name": "Digital Services Operator & CSC Citizen Facilitator",
        "qp_name": "Domestic Data Entry Operator",
        "qp_code": "SSC/Q2212",
        "nsqf_level": "NSQF Level 4",
        "ssc_name": "IT-ITeS Sector Skill Council (NASSCOM)",
        "trade_name_hi": "डिजिटल सेवा ऑपरेटर एवं सीएससी नागरिक सहायक",
        "trade_name_mr": "डिजिटल सेवा ऑपरेटर व सीएससी नागरिक सहाय्यक",
        "trade_name_pa": "ਡਿਜੀਟਲ ਸੇਵਾ ਆਪਰੇਟਰ ਅਤੇ ਸੀਐਸਸੀ ਸਹਾਇਕ",
        "min_education": ["10th", "12th", "graduate"],
        "mobility_requirement": "low",
        "sector": "IT-ITeS Sector Skill Council (NASSCOM)",
        "duration_hours": "300 Hours",
        "training_programme": "PM-AJAY Rural Digital Livelihood & e-Governance Track",
        "training_centre": "District NIELIT / Common Service Center Training Hub",
        "local_opportunity": "Village Common Service Centre (CSC) entrepreneur helping locals with DBTs, ration cards, Aadhaar, and e-Mitra",
        "skill_gaps": [
            {
                "skill": "Government Scheme e-Portals (DBT, Ration, Aadhaar, Agristack)",
                "where": "District NIELIT / CSC Academy training hub"
            },
            {
                "skill": "Advanced Data Entry Accuracy & Document Digitization Standards",
                "where": "Skill India Digital (SID) verified online practice track"
            },
            {
                "skill": "Digital Payments, Micro-ATM (AePS) Security & Cyber-Safety",
                "where": "NASSCOM Foundation / IT-ITeS SSC authorized module"
            },
            {
                "skill": "Village Level Entrepreneur (VLE) Kiosk Setup & Accounting",
                "where": "CSC e-Governance Services India training seminar"
            }
        ],
        "steps_en": [
            "Enroll in NSQF Level 4 Domestic Data Entry & Digital e-Services Course",
            "Master government portals (DBT, Ration, Aadhaar, Agristack), computer applications, and digital payments",
            "Obtain NASSCOM / NIELIT recognized certification",
            "Get fast-tracked VLE (Village Level Entrepreneur) license and setup CSC kiosk with PM-AJAY hardware grant"
        ],
        "steps_hi": [
            "NSQF लेवल 4 डिजिटल डाटा एंट्री एवं ई-सेवा कोर्स में नामांकन कराएं",
            "सरकारी पोर्टल (डीबीटी, राशन, आधार, कृषि योजनाएं) व ऑनलाइन भुगतान में निपुणता पाएं",
            "नैसकॉम/नाइलिट द्वारा प्रमाणित राष्ट्रीय प्रमाणपत्र हासिल करें",
            "वीएलई लाइसेंस प्राप्त करें और पीएम-अजय उपकरण अनुदान से गाँव में सीएससी केंद्र खोलें"
        ],
        "steps_mr": [
            "NSQF स्तर 4 डिजिटल डेटा एंट्री व ई-सेवा अभ्यासक्रमात प्रवेश घ्या",
            "शासकीय पोर्टल (डीबीटी, रेशन, आधार, कृषी योजना) व ऑनलाइन कामात पारंगत व्हा",
            "NASSCOM / NIELIT मान्यताप्राप्त प्रमाणपत्र मिळवा",
            "गाव पातळीवर सीएससी केंद्र सुरू करून दरमहा नियमित उत्पन्न मिळवा"
        ],
        "steps_pa": [
            "ਡਿਜੀਟਲ ਡਾਟਾ ਐਂਟਰੀ ਅਤੇ ਈ-ਸੇਵਾ ਕੋਰਸ ਵਿੱਚ ਦਾਖਲਾ ਲਵੋ",
            "ਸਰਕਾਰੀ ਪੋਰਟਲ ਅਤੇ ਕੰਪਿਊਟਰ ਦਾ ਕੰਮ ਸਿੱਖੋ",
            "ਨੈਸ਼ਨਲ ਸਰਟੀਫਿਕੇਟ ਹਾਸਲ ਕਰੋ",
            "ਆਪਣੇ ਪਿੰਡ ਵਿੱਚ ਸੀਐਸਸੀ ਕੇਂਦਰ ਸਥਾਪਿਤ ਕਰੋ"
        ]
    },
    "healthcare_assistant": {
        "trade_name": "General Duty Assistant (Healthcare Support)",
        "qp_name": "General Duty Assistant",
        "qp_code": "HSS/Q5101",
        "nsqf_level": "NSQF Level 4",
        "ssc_name": "Healthcare Sector Skill Council (HSSC)",
        "trade_name_hi": "जनरल ड्यूटी असिस्टेंट (स्वास्थ्य सहायता)",
        "trade_name_mr": "जनरल ड्युटी असिस्टंट (आरोग्य साहाय्यक)",
        "trade_name_pa": "ਜਨਰਲ ਡਿਊਟੀ ਅਸਿਸਟੈਂਟ (ਸਿਹਤ ਸੰਭਾਲ)",
        "min_education": ["8th", "10th", "12th", "graduate"],
        "mobility_requirement": "medium",
        "sector": "Healthcare Sector Skill Council (HSSC)",
        "duration_hours": "360 Hours",
        "training_programme": "PM-AJAY Healthcare Livelihood Track",
        "training_centre": "District Hospital & PMKK Healthcare Skill Lab",
        "local_opportunity": "Guaranteed wage employment at District Primary Health Centers, private nursing homes, or elder care services",
        "skill_gaps": [
            {
                "skill": "Clinical Patient Handling, Bed Mobility & Personal Hygiene Care",
                "where": "District Civil Hospital & PMKK Healthcare Simulation Lab"
            },
            {
                "skill": "Vital Signs Monitoring (BP, Pulse, SpO2, Temperature) & Recording",
                "where": "Healthcare Sector Skill Council (HSSC) accredited hospital"
            },
            {
                "skill": "Infection Control, Biomedical Waste Disposal & Sterile Procedures",
                "where": "District Primary Health Center internship module"
            },
            {
                "skill": "Basic Life Support (BLS) & Emergency First-Aid Triage",
                "where": "Red Cross / St. John Ambulance certified practical training"
            }
        ],
        "steps_en": [
            "Register for PM-AJAY sponsored General Duty Assistant (GDA) curriculum",
            "Complete clinical simulation, patient care, vital checks, and first aid modules",
            "Pass HSSC practical assessment with hospital internship",
            "Direct placement in District Community Health Center or accredited hospital network"
        ],
        "steps_hi": [
            "पीएम-अजय प्रायोजित जनरल ड्यूटी असिस्टेंट (GDA) कोर्स में प्रवेश लें",
            "मरीज देखभाल, प्राथमिक उपचार व वाइटल साइंस की क्लिनिकल ट्रेनिंग पूरी करें",
            "अस्पताल इंटर्नशिप के साथ स्वास्थ्य परिषद की परीक्षा पास करें",
            "जिला अस्पताल या निजी नर्सिंग होम में सीधे सम्मानजनक रोजगार प्राप्त करें"
        ],
        "steps_mr": [
            "पीएम-अजय पुरस्कृत जनरल ड्युटी असिस्टंट कोर्समध्ये नावनोंदणी करा",
            "रुग्ण सेवा, प्रथमोपचार व वैद्यकीय तपासणीचे प्रत्यक्ष प्रशिक्षण पूर्ण करा",
            "आरोग्य परिषदेचे अधिकृत प्रमाणपत्र मिळवा",
            "प्राथमिक आरोग्य केंद्र किंवा खाजगी रुग्णालयात खात्रीशीर नोकरी मिळवा"
        ],
        "steps_pa": [
            "ਜਨਰਲ ਡਿਊਟੀ ਅਸਿਸਟੈਂਟ (ਜੀਡੀਏ) ਕੋਰਸ ਵਿੱਚ ਦਾਖਲਾ ਲਵੋ",
            "ਮਰੀਜ਼ਾਂ ਦੀ ਦੇਖਭਾਲ ਅਤੇ ਮੁਢਲੀ ਸਹਾਇਤਾ ਦੀ ਸਿਖਲਾਈ ਲਵੋ",
            "ਸਿਹਤ ਕੌਂਸਲ ਵੱਲੋਂ ਸਰਟੀਫਿਕੇਟ ਪ੍ਰਾਪਤ ਕਰੋ",
            "ਜ਼ਿਲ੍ਹਾ ਹਸਪਤਾਲ ਜਾਂ ਕਲੀਨਿਕ ਵਿੱਚ ਨੌਕਰੀ ਹਾਸਲ ਕਰੋ"
        ]
    }
}

# Trade Specific Keyword Dictionaries
TRADE_KEYWORDS = {
    "food_processing": [
        "farm", "farming", "agri", "agriculture", "food", "cook", "cooking", "kheti",
        "crop", "crops", "grain", "grains", "fruit", "fruits", "pickle", "pickles",
        "processing", "dairy", "खेती", "किसान", "कृषक", "अन्न", "खाद्य", "लोणचे", "मसाले", "ਫੂਡ", "ਖੇਤੀ"
    ],
    "apparel_tailoring": [
        "tailor", "tailoring", "sew", "sewing", "stitch", "stitching", "cloth", "clothes",
        "clothing", "garment", "garments", "silai", "embroidery", "dress", "apparel",
        "सिलाई", "कपड़े", "शिलाई", "कपडे", "ਸਿਲਾਈ", "ਕੱਪੜੇ", "ਦਰਜ਼ੀ"
    ],
    "solar_technician": [
        "solar", "electric", "electrical", "wire", "wiring", "bijli", "energy", "panel",
        "panels", "surya", "suryamitra", "pv", "सोलर", "सौर", "बिजली", "वायरिंग", "ਸੋਲਰ", "ਬਿਜਲੀ"
    ],
    "automotive_ev": [
        "two-wheeler", "wheeler", "bike", "bikes", "motorcycle", "motorcycles", "vehicle", "vehicles", "car", "cars",
        "mechanic", "garage", "gaadi", "repair", "fix", "automotive", "ev", "maintenance", "scooter", "scooters",
        "गाड़ी", "मोटर", "दुरुस्ती", "ਮਕੈਨਿਕ", "ਗੱਡੀ"
    ],
    "healthcare_assistant": [
        "healthcare", "health", "nurse", "nursing", "hospital", "hospitals", "patient",
        "patients", "medical", "clinic", "clinics", "care", "caregiver", "medicine", "dawa",
        "ilaj", "दवा", "इलाज", "रुग्ण", "आरोग्य", "ਸਿਹਤ", "ਹਸਪਤਾਲ"
    ],
    "digital_csc": [
        "computer", "computers", "digital", "digitally", "internet", "online", "data", "csc",
        "phone", "cyber", "software", "कंप्यूटर", "इंटरनेट", "संगणक", "ਕੰਪਿਊਟਰ"
    ]
}

TRADE_GAP_SUMMARIES = {
    "food_processing": "Possesses agricultural intuition and raw ingredient familiarity, but lacks hygienic value-addition, preservation, and certified packaging standards required for higher market margins.",
    "apparel_tailoring": "Has basic manual garment handling exposure, but requires structured pattern making, machine maintenance, and commercial quality stitching skills for sustainable self-employment.",
    "solar_technician": "Good technical inclination; requires certified high-voltage safety protocols, inverter grid synchronization, and NSQF Level 4 PV installation credentials.",
    "automotive_ev": "Familiar with conventional mechanical tools, but lacks computerized electronic diagnostics and Electric Vehicle (EV) powertrain maintenance certification.",
    "healthcare_assistant": "High empathy and caregiving orientation; requires clinical hygiene standards, patient handling protocols, and HSSC authorized healthcare credentials.",
    "digital_csc": "Active smartphone user with digital literacy; needs formal data entry accuracy, e-governance service knowledge, and VLE certification for official government scheme facilitation."
}

ORDERED_TRADE_KEYS = [
    "food_processing",
    "apparel_tailoring",
    "solar_technician",
    "automotive_ev",
    "healthcare_assistant",
    "digital_csc"
]

def _keyword_hit(text: str, keyword: str) -> bool:
    """Helper to match keyword with word boundary for Latin and substring for Indic scripts."""
    if keyword.isascii():
        return bool(re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE))
    return keyword.lower() in text.lower()

# Canonical 5 Required Skills per Trade for Readiness Assessment
TRADE_REQUIRED_SKILLS = {
    "food_processing": [
        "Food Handling & Raw Ingredient Quality",
        "Preservation & Processing Techniques",
        "FSSAI Hygiene & Sanitation Standards",
        "Packaging & Product Labeling",
        "Micro-Enterprise Costing & Market Linkage"
    ],
    "apparel_tailoring": [
        "Basic Stitching & Fabric Cutting",
        "Commercial Pattern Drafting & Measuring",
        "Industrial Sewing Machine Operation",
        "Garment Quality Inspection & Finishing",
        "Boutique Management & Pricing"
    ],
    "solar_technician": [
        "Basic Electrical Wiring & Circuit Safety",
        "Photovoltaic Module Mounting & Alignment",
        "Electrical Safety & Earthing Protocols",
        "Inverter Diagnostics & Battery Maintenance",
        "Consumer Net-Metering & DISCOM Guidelines"
    ],
    "automotive_ev": [
        "Hand Tools & Mechanical Maintenance",
        "Two-Wheeler Engine & Brake Servicing",
        "EV Powertrain & Motor Servicing",
        "Lithium-Ion Battery & Electrical Systems",
        "Workshop Management & Billing"
    ],
    "healthcare_assistant": [
        "Patient Care & Bedside Assistance",
        "Vital Signs Monitoring (BP, Pulse, Temperature)",
        "Clinical Hygiene & Infection Control",
        "First Aid & Emergency Response",
        "Medical Records & Patient Communication"
    ],
    "digital_csc": [
        "Basic Computer Operations & Typing",
        "Government Portal Navigation (DBT, Aadhaar)",
        "Document Scanning & Digital Data Entry",
        "Online Payments & Cyber-Safety",
        "Citizen Advisory & CSC Accounting"
    ]
}

def compute_readiness_score(trade_key: str, profile_skills: List[str]) -> Tuple[int, int, int]:
    """
    Computes transparent, explainable numeric readiness score:
    (number of skills the profile already has that are relevant to the trade) / (total skills required for that trade) * 100,
    rounded to nearest integer.
    Returns (readiness_score, relevant_count, total_required).
    """
    required_skills = TRADE_REQUIRED_SKILLS.get(trade_key, [])
    total_required = len(required_skills)
    if total_required == 0:
        return 0, 0, 0

    trade_keywords = set(TRADE_KEYWORDS.get(trade_key, []))

    matched_req_indices = set()
    keyword_extra_matches = 0

    for s in profile_skills:
        s_clean = str(s).strip()
        if not s_clean:
            continue
        s_lower = s_clean.lower()

        # Check match against required skills list
        matched = False
        for idx, req in enumerate(required_skills):
            req_lower = req.lower()
            if s_lower in req_lower or req_lower in s_lower:
                matched_req_indices.add(idx)
                matched = True
                break

        if matched:
            continue

        # Check if the skill mentions any trade keywords
        if any(_keyword_hit(s_clean, kw) for kw in trade_keywords):
            keyword_extra_matches += 1

    total_relevant = len(matched_req_indices) + keyword_extra_matches
    capped_relevant = min(total_relevant, total_required)
    score = round((capped_relevant / total_required) * 100)
    return score, capped_relevant, total_required

def _matches(text: str, keywords: List[str]) -> bool:
    """Returns True if any keyword in keywords hits text with word boundaries."""
    return any(_keyword_hit(text, k) for k in keywords)

def analyze_skill_gap(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates beneficiary profile against trade criteria using a scoring engine.
    Determines recommended trade, skill gap summary, concrete gap breakdown, and NSQF alignment.
    """
    edu = (profile.get("education_level") or "").lower()
    interests = [str(i).lower() for i in profile.get("interests", [])]
    skills = [str(s).lower() for s in profile.get("skills", [])]
    family_occ = (profile.get("family_occupation") or "").lower()
    mobility = (profile.get("mobility_constraint") or "").lower()
    emp_pref = (profile.get("employment_preference") or "undecided").lower()
    location = profile.get("location") or "Your Local District"

    combined_text = " ".join(interests + skills + [family_occ, edu, mobility, emp_pref])

    # Compute match count for each trade_key using distinct keyword hits
    scores = {}
    for t_key in ORDERED_TRADE_KEYS:
        distinct_hits = sum(1 for kw in set(TRADE_KEYWORDS[t_key]) if _keyword_hit(combined_text, kw))
        scores[t_key] = distinct_hits

    max_score = max(scores.values())

    # Check mobility restriction with word boundary helper
    RESTRICTED_KEYWORDS = [
        "cannot", "restricted", "home", "near", "village", "village only",
        "local only", "low", "गाँव में", "गावातच", "दूर नहीं", "जा नहीं सकते",
        "लांब जाऊ शकत नाही", "ਨੇੜੇ", "ਪਿੰਡ ਵਿੱਚ"
    ]
    is_restricted = _matches(mobility, RESTRICTED_KEYWORDS)

    if max_score > 0:
        top_candidates = [t_key for t_key in ORDERED_TRADE_KEYS if scores[t_key] == max_score]
        if len(top_candidates) == 1:
            trade_key = top_candidates[0]
        else:
            # Tiebreak: prefer trade whose mobility_requirement matches profile restriction
            if is_restricted:
                low_mob_candidates = [t for t in top_candidates if TRADES_CATALOG[t]["mobility_requirement"] == "low"]
                trade_key = low_mob_candidates[0] if low_mob_candidates else top_candidates[0]
            else:
                trade_key = top_candidates[0]
        gap = TRADE_GAP_SUMMARIES[trade_key]
    else:
        # Default fallback based on mobility and education
        if is_restricted:
            trade_key = "food_processing"
            gap = "Beneficiary needs low-mobility, local village cluster livelihood. Skill gap exists in value-added processing and certified hygiene packaging under PM-AJAY."
        else:
            trade_key = "digital_csc" if ("10th" in edu or "12th" in edu or "graduate" in edu) else "food_processing"
            gap = "Requires formal vocational certification to bridge gap from informal labor to structured PM-AJAY livelihood pathway."

    # If mobility is strictly low and selected trade has medium mobility, fall back to low mobility trade
    if is_restricted and TRADES_CATALOG[trade_key]["mobility_requirement"] == "medium":
        trade_key = "food_processing"
        gap = f"Adapted for restricted mobility: Selected home/cluster-based Food Processing over travel-intensive trades. {gap}"

    trade = TRADES_CATALOG[trade_key]
    lang = profile.get("language", "en")

    # Localize step recommendations
    steps_key = f"steps_{lang}" if f"steps_{lang}" in trade else "steps_en"
    steps = trade.get(steps_key, trade["steps_en"])

    trade_display_name = trade.get(f"trade_name_{lang}", trade["trade_name"])

    # Spoken summary generation
    if lang == "hi":
        spoken_summary = (
            f"आपके प्रोफाइल और प्राथमिकताओं के आधार पर, आपके लिए सबसे उपयुक्त ट्रेड '{trade_display_name}' है। "
            f"यह {trade['nsqf_level']} के अंतर्गत आता है। आपको {location} के {trade['training_centre']} में "
            f"निःशुल्क प्रशिक्षण व छात्रवृत्ति मिलेगी। इसके बाद {trade['local_opportunity']} का सीधा अवसर है।"
        )
    elif lang == "mr":
        spoken_summary = (
            f"तुमच्या पार्श्वभूमीनुसार तुमच्यासाठी सर्वोत्तम पर्याय '{trade_display_name}' हा आहे. "
            f"हा {trade['nsqf_level']} अंतर्गत येतो. {location} मधील {trade['training_centre']} येथे "
            f"तुम्हाला मोफत प्रशिक्षण व विद्यावेतन मिळेल. त्यानंतर {trade['local_opportunity']} ची थेट संधी आहे."
        )
    elif lang == "pa":
        spoken_summary = (
            f"ਤੁਹਾਡੇ ਪ੍ਰੋਫਾਈਲ ਮੁਤਾਬਕ ਤੁਹਾਡੇ ਲਈ ਸਭ ਤੋਂ ਵਧੀਆ ਕੰਮ '{trade_display_name}' ਹੈ। "
            f"ਇਹ {trade['nsqf_level']} ਤਹਿਤ ਆਉਂਦਾ ਹੈ। ਤੁਹਾਨੂੰ {trade['training_centre']} ਵਿਖੇ "
            f"ਮੁਫ਼ਤ ਸਿਖਲਾਈ ਅਤੇ ਵਜ਼ੀਫ਼ਾ ਮਿਲੇਗਾ, ਜਿਸ ਤੋਂ ਬਾਅਦ ਤੁਹਾਨੂੰ ਰੋਜ਼ਗਾਰ ਦਾ ਮੌਕਾ ਮਿਲੇਗਾ।"
        )
    else:
        spoken_summary = (
            f"Based on your background and preferences, the ideal trade for you under PM-AJAY is '{trade['trade_name']}'. "
            f"Aligned with {trade['nsqf_level']}, you are eligible for 100% free training and monthly stipend at {trade['training_centre']} in {location}. "
            f"Following certification, you will be linked directly to {trade['local_opportunity']}."
        )

    # Transparent Numeric Skill Readiness Score: (relevant skills / total required) * 100
    readiness_score, relevant_count, total_required = compute_readiness_score(trade_key, profile.get("skills", []))

    return {
        "recommended_trade": trade_display_name,
        "trade_key": trade_key,
        "qp_name": trade.get("qp_name"),
        "qp_code": trade.get("qp_code"),
        "nsqf_level": trade.get("nsqf_level"),
        "ssc_name": trade.get("ssc_name"),
        "nsqf_alignment": trade["nsqf_level"],
        "gap_summary": gap,
        "readiness_score": readiness_score,
        "readiness_relevant_count": relevant_count,
        "readiness_total_required": total_required,
        "skill_gap_breakdown": trade.get("skill_gaps", []),
        "training_programme": trade["training_programme"],
        "training_centre": f"{trade['training_centre']} ({location})",
        "local_opportunity": trade["local_opportunity"],
        "roadmap_steps": steps,
        "spoken_summary": spoken_summary,
        "duration_hours": trade["duration_hours"],
        "sector": trade.get("ssc_name") or trade.get("sector")
    }
