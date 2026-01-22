from dagster import asset, AssetExecutionContext, AssetKey, Output, MetadataValue, AssetIn
from src.services.python.db import get_db_cursor
import pandas as pd
import json

DEFAULT_OWNERS = ["team:OST/spideyai-X"]



@asset(
    kinds={"python"},
    owners=DEFAULT_OWNERS,
    ins={"projects_df": AssetIn(key=AssetKey(["github", "pvt_github_project"]))},
    group_name="classification",
    required_resource_keys={"llm_classifier"},
    io_manager_key="fs_io_manager",
)
def core_match__classify_projects(context, projects_df):
    """
    Classifies GitHub projects into standardized Categories and Domains using an LLM (Phi-3.5).
    Reads from `github.pvt_github_project` and outputs classification metadata.
    """
    llm = context.resources.llm_classifier
    
    projects = []
    categories_map = {} # Name -> ID
    domains_map = {}    # Name -> ID
    
    with get_db_cursor() as cur:
        # 1. Fetch Categories & Domains for the Prompt
        cur.execute('SELECT "id", "name" FROM "public"."Category"')
        categories_map = {row["name"]: row["id"] for row in cur.fetchall()}
        
        cur.execute('SELECT "id", "name" FROM "public"."Domain"')
        domains_map = {row["name"]: row["id"] for row in cur.fetchall()}
        
        # 2. Use Projects from IO Manager
        projects = projects_df.to_dict('records')
        
        # Adjust alias manually if dataframe has 'name' but code implies 'title'
        for p in projects:
            if 'name' in p and 'title' not in p:
                p['title'] = p['name']


    context.log.info(f"Loaded {len(projects)} projects for classification.")
    
    if not projects:
        return Output(value=[], metadata={"count": 0})

    cat_names = list(categories_map.keys())
    dom_names = list(domains_map.keys())
    
    results_payload = []
    
    for p in projects:
        if not p.get('title'): continue

        try:
            # Call LLM
            result_json = llm.classify_project(
                title=p['title'], 
                project_context=p.get('context') or "", 
                categories=cat_names, 
                domains=dom_names
            )
            
            # Map strings back to IDs
            cat_name = result_json.get("category")
            dom_name = result_json.get("domain")
            cat_id = categories_map.get(cat_name)
            dom_id = domains_map.get(dom_name)
            
            if cat_id or dom_id:
                # Add classification info to the project object
                payload = {
                    "project": p,
                    "classification": {
                        "categoryId": cat_id,
                        "domainId": dom_id,
                        "categoryName": cat_name,
                        "domainName": dom_name
                    }
                }
                results_payload.append(payload)
            else:
                context.log.warning(f"LLM returned unknown labels for '{p['title']}': Cat='{cat_name}', Dom='{dom_name}'")

        except Exception as e:
            context.log.error(f"Failed to classify '{p['title']}': {e}")
            continue

    context.log.info(f"Successfully classified {len(results_payload)} projects.")
    
    return Output(
        value=results_payload, 
        metadata={
            "count": len(results_payload),
            "preview": [str(x['project']['title']) for x in results_payload[:10]]
        }
    )
