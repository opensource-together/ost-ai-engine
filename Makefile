setup:
	docker compose exec dagster-webserver bash -c " \
		prisma migrate dev && \
		npx ts-node --compiler-options '{\"module\":\"commonjs\"}' prisma/seed/seed.ts"
up:
	docker compose up -d
