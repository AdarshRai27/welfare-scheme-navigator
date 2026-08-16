"""Script to generate an expanded, production-grade dataset of Central & State Government Welfare Schemes."""

import json
import os

schemes = [
    # --- CENTRAL GOVERNMENT SCHEMES ---
    # Agriculture & Farmers Welfare
    {
        "name": "PM-Kisan Samman Nidhi",
        "issuing_body": "Ministry of Agriculture and Farmers Welfare",
        "state": "All India",
        "category": "Agriculture",
        "description": "Financial support of ₹6,000 per year paid in 3 equal installments of ₹2,000 directly to landowning farmers across India.",
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
        "description": "Provides short-term concessional credit/loans to farmers for crop cultivation, livestock farming, and fisheries at 4% interest rate.",
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
        "description": "Comprehensive crop insurance scheme protecting farmers against crop loss/damage due to natural calamities, pests, and diseases.",
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
        "description": "Promotes organic farming among farmers with financial assistance of ₹50,000 per hectare over 3 years for organic inputs and certification.",
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
        "description": "Medium-long term debt financing facility providing 3% interest subvention and credit guarantee for post-harvest management infrastructure and community farming assets.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://agriinfra.dac.gov.in"
    },

    # Business Loans & MSME Support
    {
        "name": "PM Mudra Yojana - Shishu Loan",
        "issuing_body": "Ministry of Finance",
        "state": "All India",
        "category": "Business Loan",
        "description": "Collateral-free business loans up to ₹50,000 for starting small micro-enterprises, shops, vendor businesses, and artisan units.",
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
        "description": "Comprehensive support for traditional artisans and craftspeople including 5-day skill training (₹500/day stipend), ₹15,000 toolkit e-voucher, and collateral-free loan up to ₹3 Lakhs at 5% interest rate.",
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
        "description": "Bank loans between ₹10 Lakhs and ₹1 Crore to at least one SC/ST borrower and one woman borrower per bank branch for setting up greenfield enterprises.",
        "eligibility_rules": {
            "min_age": 18
        },
        "source_url": "https://www.standupmitra.in"
    },

    # Health & Medical Care
    {
        "name": "Ayushman Bharat (PM-JAY)",
        "issuing_body": "National Health Authority",
        "state": "All India",
        "category": "Health",
        "description": "World's largest health insurance scheme providing cashless secondary and tertiary hospital care coverage up to ₹5 Lakhs per family per year across empaneled hospitals.",
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
        "description": "Provides high-quality generic medicines at 50% to 90% lower prices than branded drugs through dedicated Jan Aushadhi Kendras across India.",
        "eligibility_rules": {},
        "source_url": "https://janaushadhi.gov.in"
    },

    # Social Security & Pensions
    {
        "name": "Atal Pension Yojana (APY)",
        "issuing_body": "PFRDA / Ministry of Finance",
        "state": "All India",
        "category": "Pension",
        "description": "Guaranteed monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000, or ₹5,000 per month starting from age 60 based on monthly contributions made by unorganized sector workers.",
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

    # Women & Child Welfare
    {
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "issuing_body": "Ministry of Women and Child Development",
        "state": "All India",
        "category": "Women & Child",
        "description": "High-interest government savings scheme dedicated for girl children under 10 years, offering tax-free high returns for future higher education and marriage.",
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
        "description": "Maternity benefit scheme providing direct cash benefit of ₹5,000 to pregnant women and lactating mothers for first child birth to meet nutritional needs.",
        "eligibility_rules": {
            "min_age": 19,
            "gender": "female"
        },
        "source_url": "https://pmmvy.wcd.gov.in"
    },

    # Housing & Infrastructure
    {
        "name": "PM Awas Yojana - Gramin (PMAY-G)",
        "issuing_body": "Ministry of Rural Development",
        "state": "All India",
        "category": "Housing",
        "description": "Financial grant of ₹1.20 Lakhs (plains) to ₹1.30 Lakhs (hilly areas) for constructing pucca houses for homeless and BPL rural families.",
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

    # Education & Skill Development
    {
        "name": "PM Vidyalaxmi Scheme",
        "issuing_body": "Ministry of Education",
        "state": "All India",
        "category": "Education",
        "description": "Single-window portal providing education loans up to ₹10 Lakhs without collateral for students pursuing higher studies in premier Indian institutes.",
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
        "description": "Free industry-relevant skill training, certification, and job placement assistance for Indian youth in technologies, trades, and industry roles.",
        "eligibility_rules": {
            "min_age": 15,
            "max_age": 45
        },
        "source_url": "https://www.pmkvyofficial.org"
    },

    # Employment & Labour
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

    # --- STATE SPECIFIC WELFARE SCHEMES ---
    # UTTAR PRADESH
    {
        "name": "UP Senior Pension Scheme",
        "issuing_body": "Social Welfare Department",
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
        "issuing_body": "Women and Child Development Dept",
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
        "name": "UP Free Tablet Smartphone Yojana",
        "issuing_body": "Department of IT and Electronics",
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
        "issuing_body": "Social Welfare Department",
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
        "issuing_body": "Empowerment of Persons with Disabilities Dept",
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
        "issuing_body": "Social Welfare Department",
        "state": "Uttar Pradesh",
        "category": "Education",
        "description": "Free offline and online coaching for competitive exams (IAS, IPS, NEET, JEE, NDA, CDS) provided by senior IAS/IPS officers for needy students in UP.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 35
        },
        "source_url": "https://abhyuday.up.gov.in"
    },

    # BIHAR
    {
        "name": "Bihar Mukhyamantri Kanya Utthan Yojana",
        "issuing_body": "Education Department, Bihar",
        "state": "Bihar",
        "category": "Women & Child",
        "description": "Financial aid of ₹50,000 given to unmarried female graduates to promote female literacy and higher education in Bihar.",
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
        "description": "Collateral-free education loan up to ₹4 Lakhs at low interest rate (1% for women/PWD, 4% for others) for Class 12th pass students pursuing higher education.",
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
        "description": "Financial incentive up to ₹10 Lakhs (50% grant + 50% interest-free loan) for youth, women, SC/ST, and OBC entrepreneurs setting up new industrial units in Bihar.",
        "eligibility_rules": {
            "min_age": 18,
            "max_age": 50
        },
        "source_url": "https://udyami.bihar.gov.in"
    },

    # MAHARASHTRA
    {
        "name": "Mukhyamantri Majhi Ladki Bahin Yojana",
        "issuing_body": "Women & Child Development Dept, Maharashtra",
        "state": "Maharashtra",
        "category": "Women & Child",
        "description": "Monthly financial assistance of ₹1,500 transferred directly into bank accounts of eligible women aged 21 to 65 years in Maharashtra.",
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
        "description": "Comprehensive health insurance cover up to ₹5 Lakhs per family per year for 996 medical and surgical procedures across empaneled hospitals in Maharashtra.",
        "eligibility_rules": {
            "income_limit": 250000
        },
        "source_url": "https://www.jeevandayee.gov.in"
    },

    # RAJASTHAN
    {
        "name": "Mukhyamantri Chiranjeevi Swasthya Bima Yojana",
        "issuing_body": "Medical & Health Department, Rajasthan",
        "state": "Rajasthan",
        "category": "Health",
        "description": "Health insurance cover up to ₹25 Lakhs per family per year for secondary and tertiary hospital treatments in Rajasthan.",
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

    # MADHYA PRADESH
    {
        "name": "Mukhyamantri Ladli Behna Yojana",
        "issuing_body": "Women & Child Development Dept, MP",
        "state": "Madhya Pradesh",
        "category": "Women & Child",
        "description": "Monthly cash assistance of ₹1,250 provided to married women aged 21 to 60 years in Madhya Pradesh.",
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

    # TAMIL NADU
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

    # WEST BENGAL
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

    # KARNATAKA
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
    }
]

file_path = "backend/app/db/schemes_seed.json"
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(schemes, f, indent=4, ensure_ascii=False)

print(f"Successfully generated expanded scheme database with {len(schemes)} schemes!")
