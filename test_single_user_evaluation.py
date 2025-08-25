#!/usr/bin/env python3
"""
Script d'évaluation détaillée pour un seul utilisateur
Analyse la qualité et la diversité des recommandations
Utilise les paramètres définis dans le fichier .env
"""

import numpy as np
from src.application.services.recommendation_service import recommendation_service

def evaluate_user_recommendations(username, top_n=None):
    """Évalue les recommandations pour un utilisateur spécifique avec les paramètres .env."""
    print(f"🔍 ÉVALUATION DÉTAILLÉE POUR: {username}")
    print("=" * 80)
    
    # Utiliser top_n du .env si non spécifié
    if top_n is None:
        from src.infrastructure.config import settings
        top_n = settings.RECOMMENDATION_TOP_N
    
    # Récupérer les recommandations avec les paramètres .env
    result = recommendation_service.get_recommendations(username, top_n=top_n)
    
    if not result:
        print(f"❌ Aucune recommandation trouvée pour {username}")
        return None
    
    user = result['user']
    recommendations = result['recommendations']
    
    print(f"👤 PROFIL UTILISATEUR:")
    print(f"   Username: {user['username']}")
    print(f"   Bio: {user['bio'][:100]}...")
    print(f"   Categories: {user['categories']}")
    print(f"   Tech Stacks: {user['tech_stacks']}")
    print(f"   Projets considérés: {result['total_projects_considered']}")
    print(f"   Projets scorés: {result['total_projects_scored']}")
    
    # Analyser les scores
    semantic_scores = [rec['semantic_similarity'] for rec in recommendations]
    category_scores = [rec['category_overlap'] for rec in recommendations]
    tech_scores = [rec['tech_overlap'] for rec in recommendations]
    popularity_scores = [rec['popularity_score'] for rec in recommendations]
    combined_scores = [rec['combined_score'] for rec in recommendations]
    
    print(f"\n📊 ANALYSE DES SCORES:")
    print(f"   Score moyen combiné: {np.mean(combined_scores):.3f}")
    print(f"   Score médian combiné: {np.median(combined_scores):.3f}")
    print(f"   Écart-type combiné: {np.std(combined_scores):.3f}")
    
    print(f"\n   Similarité sémantique:")
    print(f"     - Moyenne: {np.mean(semantic_scores):.3f}")
    print(f"     - Médiane: {np.median(semantic_scores):.3f}")
    print(f"     - Min: {np.min(semantic_scores):.3f}")
    print(f"     - Max: {np.max(semantic_scores):.3f}")
    
    print(f"\n   Overlap catégoriel:")
    print(f"     - Moyenne: {np.mean(category_scores):.3f}")
    print(f"     - Médiane: {np.median(category_scores):.3f}")
    print(f"     - Projets avec catégories: {sum(1 for s in category_scores if s > 0)}/{len(category_scores)}")
    
    print(f"\n   Overlap technologique:")
    print(f"     - Moyenne: {np.mean(tech_scores):.3f}")
    print(f"     - Médiane: {np.median(tech_scores):.3f}")
    print(f"     - Projets avec tech stacks: {sum(1 for s in tech_scores if s > 0)}/{len(category_scores)}")
    
    print(f"\n   Popularité:")
    print(f"     - Moyenne: {np.mean(popularity_scores):.3f}")
    print(f"     - Médiane: {np.median(popularity_scores):.3f}")
    
    # Analyser la diversité
    languages = [rec['language'] for rec in recommendations if rec['language']]
    unique_languages = set(languages)
    
    all_categories = []
    all_tech_stacks = []
    
    for rec in recommendations:
        if rec['categories']:
            all_categories.extend([c for c in rec['categories'] if c])
        if rec['tech_stacks']:
            all_tech_stacks.extend([t for t in rec['tech_stacks'] if t])
    
    unique_categories = set(all_categories)
    unique_tech_stacks = set(all_tech_stacks)
    
    print(f"\n🎯 ANALYSE DE LA DIVERSITÉ:")
    print(f"   Langages uniques: {len(unique_languages)} ({', '.join(unique_languages)})")
    print(f"   Catégories uniques: {len(unique_categories)}")
    print(f"   Tech stacks uniques: {len(unique_tech_stacks)}")
    
    # Calculer la diversité des scores
    diversity_score = 1 - (np.std(combined_scores) / np.mean(combined_scores)) if np.mean(combined_scores) > 0 else 0
    print(f"   Score de diversité: {diversity_score:.3f} (1 = très diversifié, 0 = très concentré)")
    
    # Analyser la cohérence avec le profil utilisateur
    user_categories = set(user['categories']) if user['categories'] else set()
    user_tech_stacks = set(user['tech_stacks']) if user['tech_stacks'] else set()
    
    category_coherence = len(user_categories.intersection(unique_categories)) / len(user_categories) if user_categories else 0
    tech_coherence = len(user_tech_stacks.intersection(unique_tech_stacks)) / len(user_tech_stacks) if user_tech_stacks else 0
    
    print(f"\n🔗 COHÉRENCE AVEC LE PROFIL:")
    print(f"   Cohérence catégorielle: {category_coherence:.3f}")
    print(f"   Cohérence technologique: {tech_coherence:.3f}")
    
    # Score de qualité global
    quality_score = (
        np.mean(combined_scores) * 0.4 +
        diversity_score * 0.3 +
        category_coherence * 0.2 +
        tech_coherence * 0.1
    )
    
    print(f"\n⭐ SCORE DE QUALITÉ GLOBAL: {quality_score:.3f}/1.0")
    
    # Afficher les recommandations détaillées
    print(f"\n📋 RECOMMANDATIONS DÉTAILLÉES:")
    print("-" * 80)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i:2d}. {rec['full_name']}")
        print(f"     Score combiné: {rec['combined_score']:.3f}")
        print(f"     ├─ Sémantique: {rec['semantic_similarity']:.3f}")
        print(f"     ├─ Catégories: {rec['category_overlap']:.3f}")
        print(f"     ├─ Tech: {rec['tech_overlap']:.3f}")
        print(f"     └─ Popularité: {rec['popularity_score']:.3f}")
        print(f"     Langage: {rec['language'] or 'N/A'}")
        print(f"     Étoiles: {rec['stars']:,}")
        
        if rec['categories'] and rec['categories'] != [None]:
            print(f"     Catégories: {', '.join([str(c) for c in rec['categories'] if c])}")
        if rec['tech_stacks'] and rec['tech_stacks'] != [None]:
            print(f"     Tech Stacks: {', '.join([str(t) for t in rec['tech_stacks'] if t])}")
    
    return {
        'user': user,
        'recommendations': recommendations,
        'metrics': {
            'avg_combined_score': np.mean(combined_scores),
            'avg_semantic_score': np.mean(semantic_scores),
            'avg_category_score': np.mean(category_scores),
            'avg_tech_score': np.mean(tech_scores),
            'avg_popularity_score': np.mean(popularity_scores),
            'diversity_score': diversity_score,
            'category_coherence': category_coherence,
            'tech_coherence': tech_coherence,
            'quality_score': quality_score,
            'unique_languages': len(unique_languages),
            'unique_categories': len(unique_categories),
            'unique_tech_stacks': len(unique_tech_stacks)
        }
    }

def main():
    """Fonction principale utilisant les paramètres .env."""
    print("🔍 ÉVALUATION DÉTAILLÉE D'UN UTILISATEUR")
    print("=" * 80)
    
    # Afficher les paramètres utilisés
    from src.infrastructure.config import settings
    print(f"📋 PARAMÈTRES UTILISÉS (depuis .env):")
    print(f"   RECOMMENDATION_SEMANTIC_WEIGHT: {settings.RECOMMENDATION_SEMANTIC_WEIGHT}")
    print(f"   RECOMMENDATION_CATEGORY_WEIGHT: {settings.RECOMMENDATION_CATEGORY_WEIGHT}")
    print(f"   RECOMMENDATION_TECH_WEIGHT: {settings.RECOMMENDATION_TECH_WEIGHT}")
    print(f"   RECOMMENDATION_POPULARITY_WEIGHT: {settings.RECOMMENDATION_POPULARITY_WEIGHT}")
    print(f"   RECOMMENDATION_TOP_N: {settings.RECOMMENDATION_TOP_N}")
    print(f"   RECOMMENDATION_MAX_PROJECTS: {settings.RECOMMENDATION_MAX_PROJECTS}")
    print("=" * 80)
    
    # Test avec un utilisateur spécifique
    username = "alice_ml"  # Peut être changé
    
    # Évaluation détaillée avec les paramètres .env
    result = evaluate_user_recommendations(username)
    
    if result:
        print(f"\n✅ Évaluation terminée pour {username}")
        print(f"📊 Résumé: {len(result['recommendations'])} recommandations générées")
        print(f"⭐ Score de qualité: {result['metrics']['quality_score']:.3f}")
    else:
        print(f"❌ Échec de l'évaluation pour {username}")

if __name__ == "__main__":
    main()
