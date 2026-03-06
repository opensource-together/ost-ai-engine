#!/bin/bash

echo "🔄 Mise à jour du dossier prisma..."

# 1. Récupérer les dernières infos du repo distant
git fetch source-repo

# 2. Écraser le dossier local par celui du distant (branche develop)
git checkout source-repo/develop -- prisma

echo "✅ Dossier prisma synchronisé avec succès."