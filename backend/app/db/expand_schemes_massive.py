"""Massive Scheme Database Expansion Script for Central & All State Welfare Schemes."""

import json

schemes = [
    # ==========================================
    # 🏛️ CENTRAL GOVERNMENT WELFARE SCHEMES
    # ==========================================

    # --- Agriculture & Farmers Welfare ---
    {
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Ministry of Agriculture and Farmers Welfare",
        "state": "All India",
        "category": "Agriculture",
        "description": "Direct income support of ₹6,000 per year paid in 3 equal installments of ₹2,000 to all landholding farmer families across India.",
        "eligibility_rules": {
            "min_age": 18,
            "requires_land": True,
            "land_size_limit": 2.0
        },
        "source_url": "https://pmkisan.gov.in"
    },
    {
        "name": "Kisan Credit Card (KCC) Scheme",
        "issuing_body": "Ministry of Agriculture & NABARD",
        "state": "All India",
        "category": "Agriculture",
        "description": "Provides short-term concessional credit/loans to farmers for crop cultivation, livestock farming, and fisheries at 4% effective interest rate.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 75,
            "requires_land": False
        },
        "source_url": "https://myscheme.gov.in/schemes/kcc"
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "issuing_body": "Ministry of Agriculture and Farmers Welfare",
        "state": "All India",
        "category": "Agriculture",
        "description": "Comprehensive crop insurance scheme protecting farmers against crop loss/damage due to natural calamities, pests, and unseasonal weather.",
        "eligibility_rules": {
            "min_age": 18,
            "requires_land": False
        },
        "source_url": "https://pmfby.gov.in"
    },
    {
        "name": "Pradhan Mantri Kisan Maan-Dhan Yojana (PM-KMDY)",
        "issuing_body": "Ministry of Agriculture & LIC",
        "state": "All India",
        "category": "Pension",
        "description": "Voluntary contributory pension scheme giving a minimum assured pension of ₹3,000 per month to small and marginal farmers upon reaching 60 years.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 40,
            "land_size_limit": 2.0
        },
        "source_url": "https://pmkmy.gov.in"
    },
    {
        "name": "Paramparagat Krishi Vikas Yojana (PKVY)",
        "issuing_body": "Ministry of Agriculture",
        "state": "All India",
        "category": "Agriculture",
        "description": "Promotes organic farming among farmers with financial assistance of ₹50,000 per hectare over 3 years for organic inputs, soil health, and certification.",
        "eligibility_rules": {
            "min_age": 18,
            "requires_land": True
        },
        "source_url": "https://pgsindia-ncof.dac.gov.in"
    },
    {
        "name": "Agriculture Infrastructure Fund (AIF)",
        "issuing_body": "Ministry of Agriculture",
        "state": "All India",
        "category": "Agriculture",
        "description": "Medium-long term debt financing facility providing 3% interest subvention and credit guarantee for post-harvest management infrastructure and cold storage assets.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://agriinfra.dac.gov.in"
    },
    {
        "name": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
        "issuing_body": "Ministry of Agriculture & Jal Shakti",
        "state": "All India",
        "category": "Agriculture",
        "description": "Financial subsidy up to 55% for installing drip irrigation, micro-sprinklers, and farm ponds to maximize water use efficiency ('Per Drop More Crop').",
        "eligibility_rules": {
            "min_age": 18,
            "requires_land": True
        },
        "source_url": "https://pmksy.gov.in"
    },
    {
        "name": "Sub-Mission on Agricultural Mechanization (SMAM)",
        "issuing_body": "Ministry of Agriculture",
        "state": "All India",
        "category": "Agriculture",
        "description": "Provides 40% to 80% subsidy for purchasing tractors, power tillers, rotavators, and harvesters for small and marginal farmers.",
        "eligibility_rules": {
            "min_age": 18,
            "requires_land": True
        },
        "source_url": "https://agrimachinery.nic.in"
    },

    # --- MSME & Business Loans ---
    {
        "name": "PM Mudra Yojana - Shishu Loan",
        "issuing_body": "Ministry of Finance",
        "state": "All India",
        "category": "Business Loan",
        "description": "Collateral-free business loans up to ₹50,000 for starting small micro-enterprises, grocery shops, vendor businesses, and artisan units.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 65
        },
        "source_url": "https://www.mudra.org.in"
    },
    {
        "name": "PM Mudra Yojana - Kishor Loan",
        "issuing_body": "Ministry of Finance",
        "state": "All India",
        "category": "Business Loan",
        "description": "Collateral-free business loans above ₹50,000 and up to ₹5 Lakhs for expanding existing small businesses, workshops, and trade units.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 65
        },
        "source_url": "https://www.mudra.org.in"
    },
    {
        "name": "PM Mudra Yojana - Tarun Loan",
        "issuing_body": "Ministry of Finance",
        "state": "All India",
        "category": "Business Loan",
        "description": "Collateral-free business loans above ₹5 Lakhs and up to ₹10 Lakhs for established micro-enterprises and small manufacturing units.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 65
        },
        "source_url": "https://www.mudra.org.in"
    },
    {
        "name": "PM Vishwakarma Yojana",
        "issuing_body": "Ministry of MSME",
        "state": "All India",
        "category": "Business Loan",
        "description": "Comprehensive support for 18 traditional trade artisans including 5-day skill training (₹500/day stipend), ₹15,000 toolkit e-voucher, and collateral-free loan up to ₹3 Lakhs at 5% interest rate.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://pmvishwakarma.gov.in"
    },
    {
        "name": "PM SVANidhi (Street Vendor Loan)",
        "issuing_body": "Ministry of Housing and Urban Affairs",
        "state": "All India",
        "category": "Business Loan",
        "description": "Micro-credit facility offering collateral-free working capital loans of ₹10,000 (1st tranche), ₹20,000 (2nd tranche), and ₹50,000 (3rd tranche) with 7% interest subsidy for street vendors.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://pmsvanidhi.mohua.gov.in"
    },
    {
        "name": "PM Employment Generation Programme (PMEGP)",
        "issuing_body": "KVIC / Ministry of MSME",
        "state": "All India",
        "category": "Business Loan",
        "description": "Credit-linked subsidy scheme providing 15% to 35% margin money subsidy for establishing new micro-enterprises in manufacturing (up to ₹50 Lakhs) and service sectors (up to ₹20 Lakhs).",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://www.kviconline.gov.in/pmegpeportal"
    },
    {
        "name": "Stand Up India Scheme",
        "issuing_body": "Ministry of Finance / SIDBI",
        "state": "All India",
        "category": "Business Loan",
        "description": "Bank loans between ₹10 Lakhs and ₹1 Crore to SC/ST borrowers and women borrowers for setting up greenfield manufacturing, trading, or service enterprises.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://www.standupmitra.in"
    },
    {
        "name": "PM Formalisation of Micro Food Processing Enterprises (PMFME)",
        "issuing_body": "Ministry of Food Processing Industries",
        "state": "All India",
        "category": "Business Loan",
        "description": "Provides 35% credit-linked capital subsidy up to ₹10 Lakhs for micro food processing entrepreneurs, SHGs, and cooperatives.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://pmfme.mofpi.gov.in"
    },

    # --- Health & Medical Care ---
    {
        "name": "Ayushman Bharat (PM-JAY)",
        "issuing_body": "National Health Authority",
        "state": "All India",
        "category": "Health",
        "description": "World's largest health insurance scheme providing cashless secondary and tertiary hospital care coverage up to ₹5 Lakhs per family per year across 28,000+ empaneled hospitals.",
        "eligibility_rules": {
            "income_limit": 250000
        },
        "source_url": "https://pmjay.gov.in"
    },
    {
        "name": "PM Bharatiya Janaushadhi Pariyojana (PMBJP)",
        "issuing_body": "Department of Pharmaceuticals",
        "state": "All India",
        "category": "Health",
        "description": "Provides high-quality generic medicines at 50% to 90% lower prices than branded drugs through 10,000+ Jan Aushadhi Kendras.",
        "eligibility_rules": {},
        "source_url": "https://janaushadhi.gov.in"
    },
    {
        "name": "Ayushman Bharat Digital Mission (ABDM)",
        "issuing_body": "National Health Authority",
        "state": "All India",
        "category": "Health",
        "description": "Creates a digital health account (ABHA Health ID) for every citizen to securely store, share, and access digital health records across doctors and labs.",
        "eligibility_rules": {},
        "source_url": "https://abdm.gov.in"
    },
    {
        "name": "PM Surakshit Matritva Abhiyan (PMSMA)",
        "issuing_body": "Ministry of Health and Family Welfare",
        "state": "All India",
        "category": "Health",
        "description": "Free, quality antenatal care and health checkups provided to pregnant women on the 9th of every month at public health facilities.",
        "eligibility_rules": {
            "gender": "female"
        },
        "source_url": "https://pmsma.nhp.gov.in"
    },

    # --- Social Security & Pensions ---
    {
        "name": "Atal Pension Yojana (APY)",
        "issuing_body": "PFRDA / Ministry of Finance",
        "state": "All India",
        "category": "Pension",
        "description": "Guaranteed monthly pension of ₹1,000 to ₹5,000 per month starting from age 60 based on monthly contributions made by unorganized sector workers.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 40
        },
        "source_url": "https://www.npscra.nsdl.co.in"
    },
    {
        "name": "PM Shram Yogi Maan-Dhan (PM-SYM)",
        "issuing_body": "Ministry of Labour & Employment",
        "state": "All India",
        "category": "Pension",
        "description": "Voluntary pension scheme for unorganized workers (street vendors, domestic workers, rickshaw pullers) providing an assured monthly pension of ₹3,000 after age 60.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 40,
            "income_limit": 180000
        },
        "source_url": "https://maandhan.in"
    },
    {
        "name": "PM Suraksha Bima Yojana (PMSBY)",
        "issuing_body": "Ministry of Finance",
        "state": "All India",
        "category": "Insurance",
        "description": "Accidental insurance scheme offering ₹2 Lakh cover for accidental death or permanent full disability at an ultra-low premium of ₹20 per year.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 70
        },
        "source_url": "https://www.jansuraksha.gov.in"
    },
    {
        "name": "PM Jeevan Jyoti Bima Yojana (PMJJBY)",
        "issuing_body": "Ministry of Finance",
        "state": "All India",
        "category": "Insurance",
        "description": "Life insurance scheme offering ₹2 Lakh life cover for death due to any cause at a premium of ₹436 per year.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 50
        },
        "source_url": "https://www.jansuraksha.gov.in"
    },
    {
        "name": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS)",
        "issuing_body": "Ministry of Rural Development (NSAP)",
        "state": "All India",
        "category": "Pension",
        "description": "Central social welfare pension provided to senior citizens (60+ years) belonging to BPL households.",
        "eligibility_rules": {
            "min_age": 60,
            "income_limit": 48000
        },
        "source_url": "https://nsap.nic.in"
    },

    # --- Women & Child Welfare ---
    {
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "issuing_body": "Ministry of Women and Child Development",
        "state": "All India",
        "category": "Women & Child",
        "description": "High-interest government savings scheme dedicated for girl children under 10 years, offering 8.2% tax-free interest for higher education and marriage.",
        "eligibility_rules": {
            "min_age": 0,
            "max_age": 10,
            "gender": "female"
        },
        "source_url": "https://www.indiapost.gov.in"
    },
    {
        "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        "issuing_body": "Ministry of Women and Child Development",
        "state": "All India",
        "category": "Women & Child",
        "description": "Maternity benefit scheme providing direct cash benefit of ₹5,000 for 1st child and ₹6,000 for 2nd girl child to pregnant and lactating mothers.",
        "eligibility_rules": {
            "min_age": 19,
            "gender": "female"
        },
        "source_url": "https://pmmvy.wcd.gov.in"
    },
    {
        "name": "PM Ujjwala Yojana 2.0",
        "issuing_body": "Ministry of Petroleum & Natural Gas",
        "state": "All India",
        "category": "Energy & Power",
        "description": "Free deposit-free LPG gas connection along with 1st cylinder and hot plate free for adult women from BPL households.",
        "eligibility_rules": {
            "min_age": 18,
            "gender": "female",
            "income_limit": 150000
        },
        "source_url": "https://www.pmuy.gov.in"
    },

    # --- Housing & Infrastructure ---
    {
        "name": "PM Awas Yojana - Gramin (PMAY-G)",
        "issuing_body": "Ministry of Rural Development",
        "state": "All India",
        "category": "Housing",
        "description": "Financial grant of ₹1.20 Lakhs (plains) to ₹1.30 Lakhs (hilly areas) plus 90 days MGNREGA labor wages for constructing pucca houses for homeless rural families.",
        "eligibility_rules": {
            "income_limit": 300000
        },
        "source_url": "https://pmayg.nic.in"
    },
    {
        "name": "PM Awas Yojana - Urban (PMAY-U)",
        "issuing_body": "Ministry of Housing and Urban Affairs",
        "state": "All India",
        "category": "Housing",
        "description": "Interest subsidy up to ₹2.67 Lakhs on home loans for EWS, LIG, and MIG families constructing or buying houses in urban areas.",
        "eligibility_rules": {
            "income_limit": 600000
        },
        "source_url": "https://pmaymis.gov.in"
    },
    {
        "name": "Jal Jeevan Mission (Har Ghar Jal)",
        "issuing_body": "Ministry of Jal Shakti",
        "state": "All India",
        "category": "Social Welfare",
        "description": "Provides functional household tap connections (FHTC) delivering 55 liters of safe drinking water per capita per day to every rural household.",
        "eligibility_rules": {},
        "source_url": "https://ejalshakti.gov.in"
    },

    # --- Education & Skill Development ---
    {
        "name": "PM Vidyalaxmi Scheme",
        "issuing_body": "Ministry of Education",
        "state": "All India",
        "category": "Education",
        "description": "Single-window portal providing collateral-free education loans up to ₹10 Lakhs with 7.5% interest subvention for students admitted to quality higher education institutes.",
        "eligibility_rules": {
            "min_age": 17,
            "max_age": 30
        },
        "source_url": "https://www.vidyalakshmi.co.in"
    },
    {
        "name": "PM Kaushal Vikas Yojana (PMKVY 4.0)",
        "issuing_body": "Ministry of Skill Development",
        "state": "All India",
        "category": "Employment",
        "description": "Free industry-relevant skill training (Industry 4.0, AI, Robotics, Trades), certification, and job placement assistance for Indian youth.",
        "eligibility_rules": {
            "min_age": 15,
            "max_age": 45
        },
        "source_url": "https://www.pmkvyofficial.org"
    },
    {
        "name": "PM YASASVI Scholarship Scheme",
        "issuing_body": "Ministry of Social Justice & Empowerment",
        "state": "All India",
        "category": "Education",
        "description": "Scholarship up to ₹1.25 Lakhs per year for OBC, EBC, and DNT students studying in Class 9th to 12th in top schools across India.",
        "eligibility_rules": {
            "min_age": 13,
            "max_age": 19,
            "income_limit": 250000
        },
        "source_url": "https://yet.nta.ac.in"
    },
    {
        "name": "National Means-cum-Merit Scholarship (NMMSS)",
        "issuing_body": "Ministry of Education",
        "state": "All India",
        "category": "Education",
        "description": "Scholarship of ₹12,000 per annum (₹1,000/month) awarded to meritorious students from economically weaker sections to arrest dropouts at Class 8.",
        "eligibility_rules": {
            "min_age": 12,
            "max_age": 16,
            "income_limit": 350000
        },
        "source_url": "https://scholarships.gov.in"
    },

    # --- Labour & Employment ---
    {
        "name": "MGNREGA (Rural Employment Guarantee)",
        "issuing_body": "Ministry of Rural Development",
        "state": "All India",
        "category": "Labour Support",
        "description": "Statutory guarantee of 100 days of wage employment per financial year to rural adult household members willing to do unskilled manual work.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://nrega.nic.in"
    },
    {
        "name": "e-Shram Card Welfare Scheme",
        "issuing_body": "Ministry of Labour & Employment",
        "state": "All India",
        "category": "Labour Support",
        "description": "National database registration providing unorganized workers with a 12-digit UAN card, free accidental insurance of ₹2 Lakhs, and direct social security integration.",
        "eligibility_rules": {
            "min_age": 16,
            "max_age": 59
        },
        "source_url": "https://eshram.gov.in"
    },

    # ==========================================
    # 🗺️ STATE GOVERNMENT WELFARE SCHEMES
    # ==========================================

    # --- UTTAR PRADESH ---
    {
        "name": "UP Senior Pension Scheme",
        "issuing_body": "Social Welfare Department, UP",
        "state": "Uttar Pradesh",
        "category": "Pension",
        "description": "Monthly pension assistance of ₹1,000 per month paid directly to senior citizens aged 60 and above living below poverty threshold in UP.",
        "eligibility_rules": {
            "min_age": 60,
            "income_limit": 46080
        },
        "source_url": "https://sspy-up.gov.in"
    },
    {
        "name": "UP Kanya Sumangala Yojana",
        "issuing_body": "Women and Child Development Dept, UP",
        "state": "Uttar Pradesh",
        "category": "Women & Child",
        "description": "Conditional cash transfer of ₹15,000 given in 6 phases from birth to higher education entry for girl children in UP.",
        "eligibility_rules": {
            "min_age": 0,
            "max_age": 25,
            "gender": "female",
            "income_limit": 300000
        },
        "source_url": "https://mksy.up.gov.in"
    },
    {
        "name": "UP Free Tablet Smartphone Yojana (DigiShakti)",
        "issuing_body": "Department of IT and Electronics, UP",
        "state": "Uttar Pradesh",
        "category": "Education",
        "description": "Free tablets and smartphones distributed to final year undergraduate, diploma, and postgraduate college students in Uttar Pradesh.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 30,
            "income_limit": 200000
        },
        "source_url": "https://digishakti.up.gov.in"
    },
    {
        "name": "UP Widow Pension Scheme",
        "issuing_body": "Social Welfare Department, UP",
        "state": "Uttar Pradesh",
        "category": "Women & Child",
        "description": "Financial monthly pension support of ₹1,000 for destitute widows living in Uttar Pradesh.",
        "eligibility_rules": {
            "min_age": 18,
            "gender": "female",
            "income_limit": 200000
        },
        "source_url": "https://sspy-up.gov.in"
    },
    {
        "name": "UP Divyangjan Pension Yojana",
        "issuing_body": "Empowerment of Persons with Disabilities Dept, UP",
        "state": "Uttar Pradesh",
        "category": "Pension",
        "description": "Monthly pension assistance of ₹1,000 for disabled citizens having 40% or higher disability living in UP.",
        "eligibility_rules": {
            "min_age": 18,
            "income_limit": 46080
        },
        "source_url": "https://hsw.up.gov.in"
    },
    {
        "name": "UP Mukhyamantri Abhyudaya Yojana",
        "issuing_body": "Social Welfare Department, UP",
        "state": "Uttar Pradesh",
        "category": "Education",
        "description": "Free coaching classes for IAS, IPS, NEET, JEE, and NDA competitive exams taught by senior officers and subject experts for UP youth.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 35
        },
        "source_url": "https://abhyuday.up.gov.in"
    },
    {
        "name": "UP Vishwakarma Shram Samman Yojana",
        "issuing_body": "Department of MSME, UP",
        "state": "Uttar Pradesh",
        "category": "Business Loan",
        "description": "Free 6-day skill development training, free advanced toolkits, and margin money subsidy for traditional artisans and tradesmen in UP.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://diupmsme.upsdc.gov.in"
    },
    {
        "name": "UP Gopalak Yojana",
        "issuing_body": "Animal Husbandry Dept, UP",
        "state": "Uttar Pradesh",
        "category": "Business Loan",
        "description": "Bank loan up to ₹9 Lakhs with state interest subvention for setting up dairy farms with 10 to 20 milch animals in UP.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 55
        },
        "source_url": "https://animalhusbandry.up.gov.in"
    },

    # --- BIHAR ---
    {
        "name": "Bihar Mukhyamantri Kanya Utthan Yojana",
        "issuing_body": "Education Department, Bihar",
        "state": "Bihar",
        "category": "Women & Child",
        "description": "Financial incentive up to ₹50,000 given to unmarried female graduates to promote female literacy and higher education in Bihar.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 28,
            "gender": "female"
        },
        "source_url": "https://medhasoft.bih.nic.in"
    },
    {
        "name": "Bihar Student Credit Card Scheme",
        "issuing_body": "Bihar Education Finance Corporation",
        "state": "Bihar",
        "category": "Education",
        "description": "Collateral-free education loan up to ₹4 Lakhs at 1% interest rate (women/PWD) and 4% (others) for 12th pass students in Bihar.",
        "eligibility_rules": {
            "min_age": 17,
            "max_age": 25
        },
        "source_url": "https://www.7nishchay-yuvaupmission.bihar.gov.in"
    },
    {
        "name": "Bihar Mukhyamantri Udyami Yojana",
        "issuing_body": "Department of Industries, Bihar",
        "state": "Bihar",
        "category": "Business Loan",
        "description": "Financial incentive up to ₹10 Lakhs (50% grant + 50% interest-free loan) for youth, women, SC/ST, and OBC entrepreneurs in Bihar.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 50
        },
        "source_url": "https://udyami.bihar.gov.in"
    },
    {
        "name": "Bihar Mukhyamantri Bridhjan Pension Yojana",
        "issuing_body": "Social Welfare Dept, Bihar",
        "state": "Bihar",
        "category": "Pension",
        "description": "Monthly pension of ₹400 (age 60-79) and ₹500 (age 80+) for senior citizens in Bihar regardless of BPL/APL status.",
        "eligibility_rules": {
            "min_age": 60
        },
        "source_url": "https://elabharthi.bih.nic.in"
    },

    # --- MAHARASHTRA ---
    {
        "name": "Mukhyamantri Majhi Ladki Bahin Yojana",
        "issuing_body": "Women & Child Development Dept, Maharashtra",
        "state": "Maharashtra",
        "category": "Women & Child",
        "description": "Monthly financial grant of ₹1,500 transferred directly into bank accounts of eligible women aged 21 to 65 years in Maharashtra.",
        "eligibility_rules": {
            "min_age": 21,
            "max_age": 65,
            "gender": "female",
            "income_limit": 250000
        },
        "source_url": "https://ladkibahin.maharashtra.gov.in"
    },
    {
        "name": "Mahatma Jyotirao Phule Jan Arogya Yojana",
        "issuing_body": "State Health Assurance Society, Maharashtra",
        "state": "Maharashtra",
        "category": "Health",
        "description": "Cashless health insurance cover up to ₹5 Lakhs per family per year for 996 medical procedures across empaneled hospitals in Maharashtra.",
        "eligibility_rules": {
            "income_limit": 250000
        },
        "source_url": "https://www.jeevandayee.gov.in"
    },
    {
        "name": "Lek Ladki Yojana",
        "issuing_body": "Women & Child Development Dept, Maharashtra",
        "state": "Maharashtra",
        "category": "Women & Child",
        "description": "Financial assistance of ₹1,01,000 given in installments from birth till 18 years for yellow/orange ration card holder girls in Maharashtra.",
        "eligibility_rules": {
            "min_age": 0,
            "max_age": 18,
            "gender": "female"
        },
        "source_url": "https://mahagov.in"
    },

    # --- RAJASTHAN ---
    {
        "name": "Mukhyamantri Chiranjeevi Swasthya Bima Yojana",
        "issuing_body": "Medical & Health Department, Rajasthan",
        "state": "Rajasthan",
        "category": "Health",
        "description": "Universal health insurance cover up to ₹25 Lakhs per family per year for secondary and tertiary hospital treatments in Rajasthan.",
        "eligibility_rules": {},
        "source_url": "https://chiranjeevi.rajasthan.gov.in"
    },
    {
        "name": "Mukhyamantri Ekal Nari Samman Pension",
        "issuing_body": "Social Justice & Empowerment Dept, Rajasthan",
        "state": "Rajasthan",
        "category": "Pension",
        "description": "Monthly pension assistance ranging from ₹1,000 to ₹1,500 for widowed, divorced, or deserted women residing in Rajasthan.",
        "eligibility_rules": {
            "min_age": 18,
            "gender": "female",
            "income_limit": 48000
        },
        "source_url": "https://sjp.rajasthan.gov.in"
    },
    {
        "name": "Indira Rasoi Yojana",
        "issuing_body": "Local Self Government Dept, Rajasthan",
        "state": "Rajasthan",
        "category": "Social Welfare",
        "description": "Provides nutritious, hygienic hot meals at a highly subsidized rate of ₹8 per thali to needy urban citizens in Rajasthan.",
        "eligibility_rules": {},
        "source_url": "https://indirarasoi.rajasthan.gov.in"
    },

    # --- MADHYA PRADESH ---
    {
        "name": "Mukhyamantri Ladli Behna Yojana",
        "issuing_body": "Women & Child Development Dept, MP",
        "state": "Madhya Pradesh",
        "category": "Women & Child",
        "description": "Monthly cash assistance of ₹1,250 provided directly into bank accounts of married women aged 21 to 60 years in Madhya Pradesh.",
        "eligibility_rules": {
            "min_age": 21,
            "max_age": 60,
            "gender": "female",
            "income_limit": 250000
        },
        "source_url": "https://cmladlibehna.mp.gov.in"
    },
    {
        "name": "Mukhyamantri Sikho Kamao Yojana (MMSKY)",
        "issuing_body": "Technical Education & Skill Dept, MP",
        "state": "Madhya Pradesh",
        "category": "Employment",
        "description": "Paid apprenticeship program for youth providing skill training along with a monthly stipend of ₹8,000 to ₹10,000.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 29
        },
        "source_url": "https://mmsky.mp.gov.in"
    },
    {
        "name": "MP Ladli Laxmi Yojana 2.0",
        "issuing_body": "Women & Child Development Dept, MP",
        "state": "Madhya Pradesh",
        "category": "Women & Child",
        "description": "Cumulative financial incentive of ₹1,43,000 given to girl children from birth until higher college education in Madhya Pradesh.",
        "eligibility_rules": {
            "min_age": 0,
            "max_age": 21,
            "gender": "female"
        },
        "source_url": "https://ladlilaxmi.mp.gov.in"
    },

    # --- TAMIL NADU ---
    {
        "name": "Kalaignar Magalir Urimai Thogai Scheme",
        "issuing_body": "Special Programme Implementation Dept, Tamil Nadu",
        "state": "Tamil Nadu",
        "category": "Women & Child",
        "description": "Monthly rights grant of ₹1,000 directly transferred to eligible female heads of households in Tamil Nadu.",
        "eligibility_rules": {
            "min_age": 21,
            "gender": "female",
            "income_limit": 250000
        },
        "source_url": "https://kmut.tn.gov.in"
    },
    {
        "name": "Pudhumai Penn Scheme",
        "issuing_body": "Social Welfare & Women Empowerment Dept, TN",
        "state": "Tamil Nadu",
        "category": "Education",
        "description": "Monthly financial aid of ₹1,000 for female students who studied in government schools (Class 6-12) to pursue higher degree/diploma education.",
        "eligibility_rules": {
            "min_age": 17,
            "max_age": 25,
            "gender": "female"
        },
        "source_url": "https://penkalvi.tn.gov.in"
    },

    # --- WEST BENGAL ---
    {
        "name": "Lakshmir Bhandar Scheme",
        "issuing_body": "Women & Child Development Dept, West Bengal",
        "state": "West Bengal",
        "category": "Women & Child",
        "description": "Monthly financial assistance of ₹1,000 (General category) and ₹1,200 (SC/ST category) for female heads of households in West Bengal.",
        "eligibility_rules": {
            "min_age": 25,
            "max_age": 60,
            "gender": "female"
        },
        "source_url": "https://socialsecurity.wb.gov.in"
    },
    {
        "name": "Kanyashree Prakalpa",
        "issuing_body": "Women & Child Development Dept, West Bengal",
        "state": "West Bengal",
        "category": "Education",
        "description": "Annual scholarship of ₹1,000 (K1) and one-time grant of ₹25,000 (K2) for unmarried girls aged 13-19 years pursuing education in West Bengal.",
        "eligibility_rules": {
            "min_age": 13,
            "max_age": 19,
            "gender": "female"
        },
        "source_url": "https://wbkanyashree.gov.in"
    },
    {
        "name": "West Bengal Student Credit Card",
        "issuing_body": "Higher Education Dept, West Bengal",
        "state": "West Bengal",
        "category": "Education",
        "description": "Soft loan up to ₹10 Lakhs at 4% simple interest for students in West Bengal pursuing secondary, higher secondary, or professional higher studies.",
        "eligibility_rules": {
            "min_age": 16,
            "max_age": 40
        },
        "source_url": "https://wbscc.wb.gov.in"
    },

    # --- KARNATAKA ---
    {
        "name": "Gruha Lakshmi Scheme",
        "issuing_body": "Women & Child Development Dept, Karnataka",
        "state": "Karnataka",
        "category": "Women & Child",
        "description": "Monthly cash grant of ₹2,000 provided to woman head of every eligible family in Karnataka.",
        "eligibility_rules": {
            "min_age": 18,
            "gender": "female"
        },
        "source_url": "https://sevasindhu.karnataka.gov.in"
    },
    {
        "name": "Yuva Nidhi Scheme",
        "issuing_body": "Department of Skill Development, Karnataka",
        "state": "Karnataka",
        "category": "Employment",
        "description": "Unemployment financial allowance of ₹3,000/month for degree graduates and ₹1,500/month for diploma holders for up to 2 years.",
        "eligibility_rules": {
            "min_age": 20,
            "max_age": 30
        },
        "source_url": "https://sevasindhu.karnataka.gov.in"
    },

    # --- TELANGANA ---
    {
        "name": "Telangana Rythu Bandhu Scheme",
        "issuing_body": "Agriculture Department, Telangana",
        "state": "Telangana",
        "category": "Agriculture",
        "description": "Financial investment support of ₹10,000 per acre per year for agriculture and horticulture crops directly to farmers in Telangana.",
        "eligibility_rules": {
            "min_age": 18,
            "requires_land": True
        },
        "source_url": "https://rythubandhu.telangana.gov.in"
    },

    # --- ANDHRA PRADESH ---
    {
        "name": "YSR Rythu Bharosa Scheme",
        "issuing_body": "Agriculture Department, Andhra Pradesh",
        "state": "Andhra Pradesh",
        "category": "Agriculture",
        "description": "Financial assistance of ₹13,500 per year provided to farmer families including tenant farmers in Andhra Pradesh.",
        "eligibility_rules": {
            "min_age": 18,
            "requires_land": False
        },
        "source_url": "https://ysrrythubharosa.ap.gov.in"
    }
]

file_path = "backend/app/db/schemes_seed.json"
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(schemes, f, indent=4, ensure_ascii=False)

print(f"Successfully compiled massive scheme database with {len(schemes)} official government schemes!")
