/**
 * Test users with varied profiles to validate the recommendation pipeline.
 *
 * Each user targets a different slice of the project space so we can verify
 * that cosine-similarity + hybrid scoring returns relevant recommendations.
 */

export interface TestUser {
  name: string;
  email: string;
  bio: string;
  jobTitle: string;
  techStacks: string[];   // matched by name against public.tech_stack
  categories: string[];   // matched by name against public."Category"
  domains: string[];      // matched by name against public."Domain"
}

export const testUsersData: TestUser[] = [
  {
    name: "Alice Chen",
    email: "alice.chen@test.ost",
    bio: "Full-stack engineer focused on React and Node.js. Building modern web apps with TypeScript.",
    jobTitle: "Senior Frontend Engineer",
    techStacks: ["React", "TypeScript", "Next.js", "Node.js", "Tailwind CSS", "PostgreSQL"],
    categories: ["Web Development"],
    domains: ["Developer Tools", "E-commerce"],
  },
  {
    name: "Bob Martinez",
    email: "bob.martinez@test.ost",
    bio: "ML engineer working on NLP and computer vision. Passionate about open-source AI tooling.",
    jobTitle: "Machine Learning Engineer",
    techStacks: ["Python", "TensorFlow", "Docker", "Jupyter", "PostgreSQL"],
    categories: ["AI & Machine Learning", "Data Science & Analytics"],
    domains: ["Developer Tools", "Health & Medicine"],
  },
  {
    name: "Clara Dubois",
    email: "clara.dubois@test.ost",
    bio: "DevOps lead specializing in Kubernetes, Terraform, and CI/CD pipelines at scale.",
    jobTitle: "DevOps Lead",
    techStacks: ["Docker", "Kubernetes", "Terraform", "Go", "GitHub Actions", "AWS", "Grafana"],
    categories: ["DevOps & Cloud"],
    domains: ["Developer Tools"],
  },
  {
    name: "David Okafor",
    email: "david.okafor@test.ost",
    bio: "Mobile developer building cross-platform apps with Flutter and React Native.",
    jobTitle: "Mobile Developer",
    techStacks: ["Flutter", "Dart", "React Native", "Firebase", "TypeScript", "Kotlin"],
    categories: ["Mobile Applications"],
    domains: ["E-commerce", "Social Networks"],
  },
  {
    name: "Eva Lindström",
    email: "eva.lindstrom@test.ost",
    bio: "Security researcher and pentester. Contributing to open-source security tools.",
    jobTitle: "Security Engineer",
    techStacks: ["Python", "Rust", "Go", "Docker", "Bash"],
    categories: ["Security & Cybersecurity"],
    domains: ["Developer Tools", "Fintech"],
  },
  {
    name: "Fatima Al-Rashid",
    email: "fatima.alrashid@test.ost",
    bio: "Backend engineer with a focus on Rust systems programming and high-performance computing.",
    jobTitle: "Systems Engineer",
    techStacks: ["Rust", "C++", "Go", "Docker", "PostgreSQL", "Redis"],
    categories: ["DevOps & Cloud", "IoT & Hardware"],
    domains: ["Developer Tools", "Climate & Environment"],
  },
  {
    name: "Gabriel Costa",
    email: "gabriel.costa@test.ost",
    bio: "Data engineer building pipelines with Python and dbt. Interested in fintech analytics.",
    jobTitle: "Data Engineer",
    techStacks: ["Python", "PostgreSQL", "Docker", "AWS", "Grafana"],
    categories: ["Data Science & Analytics", "DevOps & Cloud"],
    domains: ["Fintech", "Developer Tools"],
  },
];
