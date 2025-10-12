import { PrismaClient } from '@prisma/client';
import { techStacksData } from './techstacks-data';

const prisma = new PrismaClient();

async function seedTechStacks() {
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
}

async function main() {
  await seedTechStacks();
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
