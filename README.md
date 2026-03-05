Recommender-system of the [OpenSource Together](https://github.com/opensource-together) platform.  

<div align="center">

<img width="100%" alt="ost-knight" src="https://github.com/user-attachments/assets/cdf66f76-89bf-4150-b798-e26a25dc8239" />

</div>

[![Discord](https://img.shields.io/badge/Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.com/invite/4ZDhm3dQAC) [![Follow](https://img.shields.io/twitter/follow/OpenSTogether?style=social)](https://x.com/OpenSTogether) [![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together) [![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
</div>

---

## What is it?

**OST Linker** is the AI brain behind [OpenSourceTogether](https://opensource-together.com/). It scrapes GitHub, classifies projects with LLMs, computes embeddings, and delivers personalized open-source recommendations — so you find your next contribution in seconds, not hours.

**How it works:** GitHub scraping (Go) → dbt transformations → LLM classification → vector embeddings → cosine similarity matching.

## Quick Start

```bash
cp .env.example .env              # configure
make setup                        # install deps + compile Go binaries
docker compose up --build -d      # start services (Dagster UI at :3000)
make db-init                      # apply schema + seed data
```

See the full [Contributing Guide](CONTRIBUTING.md) for local development setup.

## Tech Stack

| Layer | Tech |
|---|---|
| Orchestration | Dagster |
| Scraping | Go (scraper + fetcher) |
| Transformations | dbt (PostgreSQL) |
| Classification | LLM via OpenRouter |
| Embeddings | SentenceTransformers (MiniLM-L6-v2) |
| Similarity | pgvector (cosine) |
| Database | PostgreSQL + Prisma |

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — See [LICENSE](LICENSE).

---

<div align="center">

Built in public by [@spideystreet](https://x.com/spideystreet) & the [OST team](https://github.com/opensource-together)

</div>
