Recommender-system of the [OpenSource Together](https://github.com/opensource-together) platform.  

<div align="center">

<img width="100%" alt="ost-knight" src="https://github.com/user-attachments/assets/cdf66f76-89bf-4150-b798-e26a25dc8239" />

</div>

[![Discord](https://img.shields.io/badge/Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.com/invite/4ZDhm3dQAC) [![Follow](https://img.shields.io/twitter/follow/OpenSTogether?style=social)](https://x.com/OpenSTogether) [![GitHub](https://img.shields.io/badge/GitHub-OpenSource%20Together-black.svg)](https://github.com/opensource-together)  
</div>

---

## What is it?

**OST Linker** is the intelligence engine behind [OpenSourceTogether](https://opensource-together.com/). It helps you find your next open-source contribution in seconds, not hours.

It automatically explores the GitHub ecosystem to:
- **Spot Hidden Gems**: Surfaces high-potential projects you might miss.
- **Match Your Skills**: Understands tech stacks to recommend relevant issues.
- **Save You Time**: Filters out noise so you can focus on coding.

## Quick Start

### Prerequisites
- **Python 3.11+**
- **Poetry**
- **Docker**
- **Node.js** (for Prisma)

### Installation

1. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env and set GITHUB_ACCESS_TOKEN
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Start Database**
   ```bash
   docker-compose up -d
   ```

4. **Initialize Database**
   ```bash
   npx prisma generate
   npx prisma db push
   npx prisma db seed
   ```

5. **Run Pipeline**
   ```bash
   dagster dev
   ```

   Access the UI at [http://localhost:3000](http://localhost:3000)

## Status
Work in progress.  
Build in public here : [@spideystreet](https://x.com/spideystreet)

---

<div align="center">

Made with love by [@spideystreet](https://x.com/spideystreet) & the [OST team](https://github.com/opensource-together) for the OSS community

</div>
