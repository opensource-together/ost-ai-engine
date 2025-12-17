from dagster import asset, AssetExecutionContext, AssetKey
from src.services.python.db import get_db_cursor
import uuid

DEFAULT_OWNERS = ["team:OST/spideyai-X"]

@asset(
    kinds={"python", "postgres"},
    owners=DEFAULT_OWNERS,
    group_name="matching",
    required_resource_keys={"io_manager"},
)
def core_public__sync_projects(context, core_match__classify_projects):
    """
    Step 2: Sync / Persistence.
    
    Input: List of classified projects from `core_match__classify_projects`.
    Actions:
    1. Upsert `public.Project` (with trending=True).
    2. Upsert `match.ProjectClassification`.
    3. Upsert `public.authenticator` (Category) and `public.project_domain`.
    """
    data = core_match__classify_projects
    
    if not data:
        context.log.info("No data to sync.")
        return

    with get_db_cursor() as cur:
        # Load TechStack Map (Name -> ID)
        cur.execute('SELECT "id", "name" FROM "public"."tech_stack"')
        tech_stack_map = {row["name"].lower(): row["id"] for row in cur.fetchall()}

    synced_count = 0
    
    for item in data:
        p = item["project"]
        classification = item["classification"]
        
        cat_id = classification["categoryId"]
        dom_id = classification["domainId"]
        
        # Combine languages (dict keys) and topics (list)
        # languages is typically JSON like {"Python": 1000, "Rust": 500}
        # topics is JSON list ["machine-learning", "python"]
        
        project_tech_names = set()
        
        langs = p.get("languages")
        if langs:
            if isinstance(langs, dict):
                project_tech_names.update(k.lower() for k in langs.keys())
            elif isinstance(langs, list):
                # If list of strings
                if langs and isinstance(langs[0], str):
                    project_tech_names.update(l.lower() for l in langs)
                # If list of dicts (unlikely but possible), adapt if needed
                # else: pass 
            
        if p.get("topics"):
            project_tech_names.update(t.lower() for t in p["topics"])
            
        
        try:
            # Use a separate transaction per project to isolate failures
            with get_db_cursor(commit=True) as cur:
                # A. Upsert public.Project
                # Force trending = True
                cur.execute("""
                    INSERT INTO "public"."Project" (
                        "id", 
                        "title", 
                        "description", 
                        "repoUrl", 
                        "provider", 
                        "githubUrl", 
                        "published",
                        "trending", 
                        "createdAt", 
                        "updatedAt"
                    )
                    VALUES (%s, %s, %s, %s, 'GITHUB', %s, true, true, %s, NOW())
                    ON CONFLICT ("id") DO UPDATE SET
                        "title" = EXCLUDED."title",
                        "description" = EXCLUDED."description",
                        "repoUrl" = EXCLUDED."repoUrl",
                        "githubUrl" = EXCLUDED."githubUrl",
                        "trending" = true,
                        "updatedAt" = NOW();
                """, (
                    p['id'],
                    p['title'],
                    p['description'],
                    p['url'],
                    p['url'], # githubUrl
                    p['created_at']
                ))
                
                # B. Upsert match.project_classification
                match_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO "match"."project_classification" (
                        "id", "projectId", "categoryId", "domainId", 
                        "createdAt", "updatedAt"
                    )
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT ("projectId") DO UPDATE SET
                        "categoryId" = EXCLUDED."categoryId",
                        "domainId" = EXCLUDED."domainId",
                        "updatedAt" = NOW();
                """, (match_id, p['id'], cat_id, dom_id))
                
                # C. Relations
                
                # 1. Category -> public.project_category
                if cat_id:
                    cur.execute("""
                        INSERT INTO "public"."project_category" ("id", "projectId", "categoryId", "createdAt")
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT ("projectId", "categoryId") DO NOTHING;
                    """, (str(uuid.uuid4()), p['id'], cat_id))
                    
                # 2. Domain -> public.project_domain
                if dom_id:
                    cur.execute("""
                        INSERT INTO "public"."project_domain" ("id", "projectId", "domainId", "createdAt")
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT ("projectId", "domainId") DO NOTHING;
                    """, (str(uuid.uuid4()), p['id'], dom_id))
                
                # 3. Tech Stacks -> public.project_tech_stack
                for name in project_tech_names:
                    ts_id = tech_stack_map.get(name)
                    if ts_id:
                        cur.execute("""
                            INSERT INTO "public"."project_tech_stack" ("id", "projectId", "techStackId", "createdAt")
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT ("projectId", "techStackId") DO NOTHING;
                        """, (str(uuid.uuid4()), p['id'], ts_id))

            synced_count += 1
            
        except Exception as e:
            context.log.error(f"Failed to sync '{p.get('title')}': {e}")
                
    context.log.info(f"Sync Complete. Persisted {synced_count} projects, classifications, and tech stacks.")
