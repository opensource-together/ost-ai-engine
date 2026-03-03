Recommender-system of the [OpenSource Together](https://github.com/opensource-together) platform.  

<div align="center">

<img width="100%" alt="ost-knight" src="https://github.com/user-attachments/assets/cdf66f76-89bf-4150-b798-e26a25dc8239" />

</div>

[![Discord](https://img.shields.io/badge/Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.com/invite/4ZDhm3dQAC) [![Follow](https://img.shields.io/twitter/follow/OpenSTogether?style=social)](https://x.com/OpenSTogether) [![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together) [![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
</div>

---

## What is it?

**OST Linker** is the intelligence engine behind [OpenSourceTogether](https://opensource-together.com/). It helps you find your next open-source contribution in seconds, not hours.

It automatically explores the GitHub ecosystem to:
- **Spot Hidden Gems**: Surfaces high-potential projects you might miss.
- **Match Your Skills**: Understands tech stacks to recommend relevant issues.
- **Save You Time**: Filters out noise so you can focus on coding.

## Quick Start

1. **Configuration**
   Copy `.env.example` to `.env` and adjust values.
   ```bash
   cp .env.example .env
   ```

2. **Start the Platform**
   Launch all services :
   ```bash
   docker compose up --build -d
   ```
   
   *Dagster UI will be available at [http://localhost:3000](http://localhost:3000).*

3. **Initialize Database**
   Apply the Schema and seed initial data (TechStacks, Categories, etc.):
   ```bash
   npx prisma db push
   npx ts-node prisma/seed/seed.ts
   ```
   *(Ensure you have Node.js installed locally. The DB is exposed on port 5433 by default).*

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## Status

Work in progress.
Build in public here : [@spideystreet](https://x.com/spideystreet)

## License

This project is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). See [LICENSE](LICENSE) for details.

---

<div align="center">

Made with love by [@spideystreet](https://x.com/spideystreet) & the [OST team](https://github.com/opensource-together) for the OSS community

</div>
