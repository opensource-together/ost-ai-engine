import uuid
import json
import random
from typing import List, Dict, Any
from src.services.python.db import get_db_cursor
from datetime import datetime

# Reference Data from prisma/seed/*-data.ts

# Source: domains-data.ts
DOMAINS_DATA = [
  "Health & Medicine", "E-commerce", "Fintech", "Education", "Social Networks",
  "Productivity", "Blockchain & Crypto", "Developer Tools", "Climate & Environment",
  "Logistics & Supply chain", "Agritech", "Art & Creative"
]

# Source: categories-data.ts
CATEGORIES_DATA = [
  "AI & Machine Learning", "Web Development", "Mobile Applications", "DevOps & Cloud",
  "Security & Cybersecurity", "IoT & Hardware", "Data Science & Analytics",
  "Virtual Reality / Augmented Reality", "Software Testing & Quality"
]

# Source: techstacks-data.ts (Subset for profiles)
# Note: Ensure names match exactly what's in techstacks-data.ts
TECH_STACKS_DATA = {
    "Web": [
        ("React", "TECH"), ("Vue", "TECH"), ("Next.js", "TECH"), ("Tailwind CSS", "TECH"), ("TypeScript", "LANGUAGE"),
        ("Node.js", "TECH"), ("PostgreSQL", "TECH"), ("Sass", "TECH")
    ],
    "Data": [
        ("Python", "LANGUAGE"), ("Pandas", "TECH"), ("GraphQL", "TECH"), ("PostgreSQL", "TECH"), ("TensorFlow", "TECH"), ("Jupyter", "TECH")
    ],
    "Mobile": [
        ("Flutter", "TECH"), ("React Native", "TECH"), ("Swift", "LANGUAGE"), ("Kotlin", "LANGUAGE"), ("Dart", "LANGUAGE")
    ],
    "DevOps": [
        ("Docker", "TECH"), ("Kubernetes", "TECH"), ("AWS", "TECH"), ("Terraform", "TECH"), ("GitHub Actions", "TECH"), ("Bash", "LANGUAGE")
    ],
    "Security": [
        ("Python", "LANGUAGE"), ("Bash", "LANGUAGE"), ("Go", "LANGUAGE"), ("Rust", "LANGUAGE")
    ]
}

# Profiles mapping to valid Domains and Categories
PROFILES = [
    {
        "jobTitle": "Senior Frontend Engineer",
        "bio": "Building sleek e-commerce experiences.",
        "focus": "Web",
        "domain": "E-commerce",
        "category": "Web Development"
    },
    {
        "jobTitle": "Data Scientist",
        "bio": "Analyzing climate data models.",
        "focus": "Data",
        "domain": "Climate & Environment",
        "category": "Data Science & Analytics"
    },
    {
        "jobTitle": "Fintech Backend Dev",
        "bio": "Secure payments and ledger logic.",
        "focus": "Web", # Backend fits in web stack usually or generic
        "domain": "Fintech",
        "category": "Web Development"
    },
    {
        "jobTitle": "DevOps Engineer",
        "bio": "Scaling developer tools infrastructure.",
        "focus": "DevOps",
        "domain": "Developer Tools",
        "category": "DevOps & Cloud"
    },
    {
        "jobTitle": "Mobile Architect",
        "bio": "Health tracking app development.",
        "focus": "Mobile",
        "domain": "Health & Medicine",
        "category": "Mobile Applications"
    },
    {
        "jobTitle": "Security Researcher",
        "bio": "Blockchain security auditing.",
        "focus": "Security",
        "domain": "Blockchain & Crypto",
        "category": "Security & Cybersecurity"
    },
    {
        "jobTitle": "EdTech Fullstack",
        "bio": "Improving education through technology.",
        "focus": ["Web", "Data"],
        "domain": "Education",
        "category": "Web Development"
    },
     {
        "jobTitle": "Creative Coder",
        "bio": "Generative art and interactive web.",
        "focus": "Web",
        "domain": "Art & Creative",
        "category": "Web Development"
    },
    {
        "jobTitle": "Logistics Platform Lead",
        "bio": "Optimizing supply chains with AI.",
        "focus": ["Web", "Data"],
        "domain": "Logistics & Supply chain",
        "category": "AI & Machine Learning"
    },
    {
        "jobTitle": "IoT Engineer",
        "bio": "Smart agriculture solutions.",
        "focus": ["DevOps", "Data"], # IoT often involves lower level or ops
        "domain": "Agritech",
        "category": "IoT & Hardware"
    }
]

def fetch_reference_data(cur):
    """Fetch existing Domains, Categories, TechStacks maps (Name -> ID)"""
    
    # 1. Domains
    domain_map = {}
    print("Fetching existing Domains...")
    cur.execute('SELECT "id", "name" FROM "public"."Domain"')
    for row in cur.fetchall():
        domain_map[row['name']] = row['id']

    # 2. Categories
    category_map = {}
    print("Fetching existing Categories...")
    cur.execute('SELECT "id", "name" FROM "public"."Category"')
    for row in cur.fetchall():
        category_map[row['name']] = row['id']

    # 3. TechStacks
    tech_map = {}
    print("Fetching existing TechStacks...")
    cur.execute('SELECT "id", "name" FROM "public"."tech_stack"')
    for row in cur.fetchall():
        tech_map[row['name']] = row['id']

    return domain_map, category_map, tech_map

def generate_users(count=10):
    print(f"Generating users based on {len(PROFILES)} profiles using EXISTING reference data...")
    with get_db_cursor(commit=True) as cur:
        # FETCH instead of INSERT
        domain_map, category_map, tech_map = fetch_reference_data(cur)
        
        # Determine how many multiples of profiles we need
        loops = (count // len(PROFILES)) + 1
        
        generated_count = 0
        for _ in range(loops):
            for profile in PROFILES:
                if generated_count >= count:
                    break
                
                uid = str(uuid.uuid4())
                name = f"User {generated_count+1} {profile['jobTitle']}"
                email = f"user{generated_count+1}_{random.randint(1000,9999)}@example.com"
                username = f"user{generated_count+1}_{random.randint(1000,9999)}"
                
                print(f"Creating user: {name} ({profile['domain']} - {profile['category']})")
                cur.execute("""
                    INSERT INTO "public"."user" (
                        "id", "name", "email", "jobTitle", "bio", "githubUsername", 
                        "emailVerified", "createdAt", "updatedAt"
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, 
                        false, NOW(), NOW()
                    )
                """, (uid, name, email, profile['jobTitle'], profile['bio'], username))

                # Link Domain
                if profile['domain'] in domain_map:
                    cur.execute("""
                        INSERT INTO "public"."user_domain" ("id", "userId", "domainId")
                        VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
                    """, (str(uuid.uuid4()), uid, domain_map[profile['domain']]))
                else:
                    print(f"Warning: Domain '{profile['domain']}' not found in DB.")

                # Link Category
                if profile['category'] in category_map:
                    cur.execute("""
                        INSERT INTO "public"."user_categories" ("id", "userId", "categoryId")
                        VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
                    """, (str(uuid.uuid4()), uid, category_map[profile['category']]))
                else:
                    print(f"Warning: Category '{profile['category']}' not found in DB.")

                # Link TechStack
                focus_areas = profile['focus']
                if isinstance(focus_areas, str):
                    focus_areas = [focus_areas]
                
                chosen_techs = []
                for focus in focus_areas:
                    if focus in TECH_STACKS_DATA:
                        available = TECH_STACKS_DATA[focus]
                        # Pick 3-5 random techs
                        chosen_techs.extend(random.sample(available, min(len(available), random.randint(3, 5))))
                
                chosen_techs = list(set(chosen_techs))

                for tech_name, _ in chosen_techs:
                    if tech_name in tech_map:
                        cur.execute("""
                            INSERT INTO "public"."user_tech_stack" ("id", "userId", "techStackId")
                            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
                        """, (str(uuid.uuid4()), uid, tech_map[tech_name]))
                    else:
                         # Optional: log missing tech stack if verbose
                         pass

                generated_count += 1

    print(f"Success! {generated_count} users seeded and linked to existing attributes.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    generate_users(10)
