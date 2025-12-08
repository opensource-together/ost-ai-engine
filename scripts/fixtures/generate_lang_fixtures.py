import sys
import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.python.db import get_db_cursor

def generate_lang_fixtures():
    print("Generating fixtures for analytics.stg_github_project...")
    
    fixtures = [
        # 1. Clear English Project (Should be ACCEPTED)
        {
            "name": "fast-api-starter",
            "description": "A comprehensive starter kit for FastAPI applications with Docker, Postgres, and Redis support. Includes authentication and testing patterns.",
            "language": "Python",
            "url": "https://github.com/ost/fast-api-starter"
        },
        # 2. Clear Chinese Project (Should be REJECTED - Blacklisted)
        {
            "name": "vue-admin-beautiful",
            "description": "一款基于vue3.0+ant-design-vue+typescript的后台管理系统",
            "language": "Vue",
            "url": "https://github.com/ost/vue-admin-beautiful"
        },
        # 3. Mixed Content - Mostly English (Should be ACCEPTED)
        {
            "name": "global-tool",
            "description": "Global utility for data processing. 支持中文 comments but mostly English documentation and logic.",
            "language": "Go",
            "url": "https://github.com/ost/global-tool"
        },
        # 4. Mixed Content - Mostly Chinese (Should be REJECTED if confidence > 30%)
        {
            "name": "easy-deploy",
            "description": "简单易用的部署工具。Easy to use deployment tool. 自动化运维，一键发布。",
            "language": "Shell",
            "url": "https://github.com/ost/easy-deploy"
        },
        # 5. No Description (Should be ACCEPTED but with null language)
        {
            "name": "minimal-repo",
            "description": None,
            "language": "C",
            "url": "https://github.com/ost/minimal-repo"
        },
        # 6. Non-Latin Script in Name (Should be REJECTED - Immediate Regex Filter)
        {
            "name": "测试项目",
            "description": "Test project with non-latin name.",
            "language": "Java",
            "url": "https://github.com/ost/test-project-cn"
        },
        # 7. Japanese Project (Should be REJECTED - Blacklisted)
        {
            "name": "react-native-jp",
            "description": "React Nativeのための日本語ドキュメントとサンプルコード。",
            "language": "JavaScript",
            "url": "https://github.com/ost/react-native-jp"
        },
        # 8. Arabic Project (Should be REJECTED - Blacklisted)
        {
            "name": "laravel-ar",
            "description": "مكتبة لمساعدة المطورين العرب في بناء تطبيقات لارافيل",
            "language": "PHP",
            "url": "https://github.com/ost/laravel-ar"
        },
        # 9. Short English Description (Should be ACCEPTED)
        {
            "name": "utils",
            "description": "Small utility functions.",
            "language": "TypeScript",
            "url": "https://github.com/ost/utils"
        },
        # 10. French Project (Should be ACCEPTED - Latin script, not blacklisted)
        {
            "name": "analyse-donnees",
            "description": "Outil d'analyse de données pour les entreprises françaises. Supporte l'export CSV.",
            "language": "Python",
            "url": "https://github.com/ost/analyse-donnees"
        },
        # 11. Russian Project (Should be REJECTED - Blacklisted)
        {
            "name": "yandex-sdk",
            "description": "Библиотека для работы с API Яндекс.Карт и других сервисов.",
            "language": "Python",
            "url": "https://github.com/ost/yandex-sdk"
        },
        # 12. Hindi Project (Should be REJECTED - Blacklisted)
        {
            "name": "hindi-nlp",
            "description": "प्राकृतिक भाषा प्रसंस्करण के लिए एक पायथन लाइब्रेरी।",
            "language": "Python",
            "url": "https://github.com/ost/hindi-nlp"
        }
    ]

    with get_db_cursor(commit=True) as cur:
        for proj in fixtures:
            # On génère un ID seulement si c'est une nouvelle insertion (si nécessaire)
            # Mais pour l'upsert, PostgreSQL gérera l'ID existant si on n'update pas la PK
            # Check if project exists by URL
            cur.execute('SELECT id FROM "analytics"."stg_github_project" WHERE url = %s', (proj["url"],))
            existing = cur.fetchone()

            if existing:
                # Update existing project
                cur.execute(
                    """
                    UPDATE "analytics"."stg_github_project"
                    SET "description" = %s,
                        "stars" = %s,
                        "forks" = %s,
                        "topics" = %s,
                        "updated_at" = NOW()
                    WHERE "url" = %s
                    """,
                    (
                        proj["description"],
                        100,
                        10,
                        json.dumps(["test", "fixture"]),
                        proj["url"]
                    )
                )
                print(f"Updated: {proj['name']}")
            else:
                # Insert new project
                proj_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO "analytics"."stg_github_project" 
                    ("id", "name", "description", "url", "stars", "forks", "language", "topics", "created_at", "updated_at")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """,
                    (
                        proj_id,
                        proj["name"],
                        proj["description"],
                        proj["url"],
                        100, 
                        10,  
                        proj["language"],
                        json.dumps(["test", "fixture"]),
                    )
                )
                print(f"Inserted: {proj['name']}")

    print("Done! Fixtures generated.")

if __name__ == "__main__":
    generate_lang_fixtures()
