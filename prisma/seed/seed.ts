import { PrismaClient } from '@prisma/client';
import { techStacksData } from './techstacks-data';
import { categoriesData } from './categories-data';
import { domainsData } from './domains-data';
import { testUsersData } from './users-data';

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

  // --- Test Users ---
  console.log('Seeding test users...');

  // Build lookup maps: name -> id
  const allTechStacks = await prisma.techStack.findMany();
  const tsMap = new Map(allTechStacks.map((t) => [t.name, t.id]));

  const allCategories = await prisma.category.findMany();
  const catMap = new Map(allCategories.map((c) => [c.name, c.id]));

  const allDomains = await prisma.domain.findMany();
  const domMap = new Map(allDomains.map((d) => [d.name, d.id]));

  for (const userData of testUsersData) {
    const user = await prisma.user.upsert({
      where: { email: userData.email },
      update: {
        name: userData.name,
        bio: userData.bio,
        jobTitle: userData.jobTitle,
      },
      create: {
        name: userData.name,
        email: userData.email,
        bio: userData.bio,
        jobTitle: userData.jobTitle,
      },
    });

    // Link tech stacks
    for (const tsName of userData.techStacks) {
      const tsId = tsMap.get(tsName);
      if (!tsId) {
        console.warn(`  ⚠ Tech stack "${tsName}" not found, skipping`);
        continue;
      }
      await prisma.userTechStack.upsert({
        where: { userId_techStackId: { userId: user.id, techStackId: tsId } },
        update: {},
        create: { userId: user.id, techStackId: tsId },
      });
    }

    // Link categories
    for (const catName of userData.categories) {
      const catId = catMap.get(catName);
      if (!catId) {
        console.warn(`  ⚠ Category "${catName}" not found, skipping`);
        continue;
      }
      await prisma.userCategories.upsert({
        where: { userId_categoryId: { userId: user.id, categoryId: catId } },
        update: {},
        create: { userId: user.id, categoryId: catId },
      });
    }

    // Link domains
    for (const domName of userData.domains) {
      const domId = domMap.get(domName);
      if (!domId) {
        console.warn(`  ⚠ Domain "${domName}" not found, skipping`);
        continue;
      }
      await prisma.userDomains.upsert({
        where: { userId_domainId: { userId: user.id, domainId: domId } },
        update: {},
        create: { userId: user.id, domainId: domId },
      });
    }

    console.log(`  ✅ ${userData.name} (${userData.techStacks.length} techs, ${userData.categories.length} cats, ${userData.domains.length} doms)`);
  }

  console.log(`✅ Seeded ${testUsersData.length} test users`);
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
