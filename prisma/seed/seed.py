from prisma import Prisma
from pathlib import Path
import json
import sys

client = Prisma()

def find_model(client_obj, candidates):
    for name in candidates:
        if hasattr(client_obj, name):
            return getattr(client_obj, name)
    return None


def main():
    p = Path(__file__).with_name("techstacks-data.json")
    if not p.exists():
        print(f"Data file not found: {p}")
        sys.exit(1)

    data = json.loads(p.read_text())

    # connect the client (sync interface expected, generator uses interface = "sync")
    client.connect()
    try:
        # Try likely model attribute names
        model = find_model(client, ["tech_stack", "TechStack", "techstack"])
        if model is None:
            print("Could not find TechStack model on the Prisma client. Did you run `npx prisma generate`?")
            sys.exit(1)

        print("Seeding tech stacks...")
        for t in data:
            where = {"name": t["name"]}
            update = {"iconUrl": t["iconUrl"], "type": t["type"]}
            create = {"name": t["name"], "iconUrl": t["iconUrl"], "type": t["type"]}

            # Upsert using the model
            model.upsert(where=where, data={"create": create, "update": update})

        print(f"✅ Seeded {len(data)} tech stacks")

        # Seed Categories
        p_cat = Path(__file__).with_name("categories-data.json")
        if p_cat.exists():
            data_cat = json.loads(p_cat.read_text())
            model_cat = find_model(client, ["category", "Category"])
            
            if model_cat:
                print("Seeding categories...")
                for c in data_cat:
                    where = {"name": c["name"]}
                    create = {"name": c["name"]}
                    model_cat.upsert(where=where, data={"create": create, "update": {}})
                print(f"✅ Seeded {len(data_cat)} categories")
            else:
                print("⚠️  Category model not found, skipping categories.")
        else:
            print(f"⚠️  Categories data file not found: {p_cat}")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
