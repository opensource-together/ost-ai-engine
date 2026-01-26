import { PrismaClient } from '@prisma/client';
import { techStacksData } from './techstacks-data';
import { categoriesData } from './categories-data';
import { domainsData } from './domains-data';

const prisma = new PrismaClient();

async function seed() {
  console.log('Seeding tech stacks...');

  for (const techStack of techStacksData) {
    await prisma.techStack.upsert({
      where: { name: techStack.name },
      update: {
        iconUrl: techStack.iconUrl,
        type: techStack.type,
      },
      create: {
        name: techStack.name,
        iconUrl: techStack.iconUrl,
        type: techStack.type,
      },
    });
  }
  console.log(`✅ Seeded ${techStacksData.length} tech stacks`);

  console.log('Seeding categories...');
  for (const category of categoriesData) {
    await prisma.category.upsert({
      where: { name: category.name },
      update: {},
      create: {
        name: category.name,
      },
    });
  }
  console.log(`✅ Seeded ${categoriesData.length} categories`);

  console.log('Seeding domains...');
  for (const domain of domainsData) {
    await prisma.domain.upsert({
      where: { name: domain.name },
      update: {},
      create: {
        name: domain.name,
      },
    });
  }
  console.log(`✅ Seeded ${domainsData.length} domains`);
}

async function main() {
  await seed();
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
