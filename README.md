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
cp .env.example .env              # configure environment
make setup                        # install deps + compile Go binaries
npm ci                            # Prisma / ts-node (package.json is in-repo)
docker compose up --build -d      # start services (Dagster UI at :3000)
make db-init                      # apply schema + seed data
```

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to propose changes, run checks, and open PRs.

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — See [LICENSE](LICENSE).

---

<div align="center">

Built in public by [@spideystreet](https://x.com/spideystreet) & the [OST team](https://github.com/opensource-together)

</div>
