Recommender-system of the [OpenSource Together](https://github.com/opensource-together) platform.  

<div align="center">

<img width="100%" alt="ost-knight" src="https://github.com/user-attachments/assets/cdf66f76-89bf-4150-b798-e26a25dc8239" />

</div>

[![Discord](https://img.shields.io/badge/Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.com/invite/4ZDhm3dQAC) [![Follow](https://img.shields.io/twitter/follow/OpenSTogether?style=social)](https://x.com/OpenSTogether) [![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together)  
</div>

---

## What is it?

An AI‑powered data pipeline that discovers, understands, and curates open‑source projects to power OST’s recommendation system and provide high-quality projects to contribute on.

What it does :
- **Discover**: scan GitHub at scale with Golang scrapers
- **Understand**: detect language and semantics (fastText + transformers)
- **Assess**: score quality and relevance from activity and metadata signals
- **Enrich**: normalize topics, tech stacks, and fields into a coherent schema

**Deliver**: output a clean, queryable dataset (PostgreSQL via Prisma)

## Quick Start

1. Copy `.env.example` into `.env` and fill it.
2. Copy `config/cfg_example.py` to `config/cfg.py` and adjust the config to your personal parameters.
3. Start
```bash
# Start the engine
docker compose up
```

Dagster UI : http://localhost:3000

## Status
Work in progress.  
Build in public here : [@spideyX](https://x.com/spideyai_X)

---

<div align="center">

Made with love by [@spideyX](https://x.com/spideyai_X) & the [OST team](https://github.com/opensource-together) for the OSS community

</div>
