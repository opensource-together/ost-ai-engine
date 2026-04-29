Recommender-system of the [OpenSource Together](https://github.com/opensource-together) platform.  

<div align="center">

<img width="100%" alt="ost-knight" src="https://github.com/user-attachments/assets/cdf66f76-89bf-4150-b798-e26a25dc8239" />

</div>

[![Discord](https://img.shields.io/badge/Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.com/invite/4ZDhm3dQAC) [![Follow](https://img.shields.io/twitter/follow/OpenSTogether?style=social)](https://x.com/OpenSTogether) [![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together) [![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
</div>

---

## What is OST Linker?

The AI-powered recommendation engine behind [OpenSourceTogether](https://opensource-together.com/).

It analyzes open-source projects and matches them to contributors — so you find your next contribution in seconds, not hours.


## Getting Started

```bash
cp .env.example .env              # set DATABASE_URL, tokens, optional host ports (see file + AGENTS.md)
make setup                        # uv sync + compile Go binaries
npm ci                            # Prisma / Node (needed before db-init)
docker compose up --build -d      # Dagster + API + db (default host: Dagster :3000, API :8000 unless overridden in .env)
make db-init                      # Prisma schema + seed
make ci-check                     # Python parity with CI quality job (before a PR); full CI is broader — see AGENTS.md
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) (branch flow, conventions, **`make ci-check`**). For command cheat-sheets (**dbt**, API, Docker overrides), see [AGENTS.md](AGENTS.md).

## License

The code in this repository is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — see [LICENSE](LICENSE). That license allows sharing and adapting the work for **non-commercial** use; it is **not** the same as [OSI’s definition](https://opensource.org/osd) of “open source.” For commercial licensing or other permission questions, use the channels in [CONTRIBUTING.md](CONTRIBUTING.md).

---

<div align="center">

Built in public by [@spideystreet](https://x.com/spideystreet) & the [OST team](https://github.com/opensource-together)

</div>
