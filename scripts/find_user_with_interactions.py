#!/usr/bin/env python3
"""
Script to find users with interactions for API testing.
"""

import sys
sys.path.append('../src')

from sqlalchemy.orm import Session
from src.infrastructure.postgres.database import SessionLocal
from src.domain.models.schema import User, TeamMember, Contribution, Application

def find_users_with_interactions():
    """Find users who have interactions (team memberships, contributions, applications)."""
    
    db = SessionLocal()
    try:
        # Find users with team memberships
        team_users = db.query(TeamMember.user_id).distinct().all()
        team_user_ids = [user[0] for user in team_users]
        
        # Find users with contributions
        contribution_users = db.query(Contribution.user_id).distinct().all()
        contribution_user_ids = [user[0] for user in contribution_users]
        
        # Find users with applications
        application_users = db.query(Application.user_id).distinct().all()
        application_user_ids = [user[0] for user in application_users]
        
        # Combine all user IDs
        all_user_ids = set(team_user_ids + contribution_user_ids + application_user_ids)
        
        print(f"📊 Users with interactions:")
        print(f"   - Team memberships: {len(team_user_ids)}")
        print(f"   - Contributions: {len(contribution_user_ids)}")
        print(f"   - Applications: {len(application_user_ids)}")
        print(f"   - Total unique users: {len(all_user_ids)}")
        
        if all_user_ids:
            print(f"\n🎯 Users with interactions:")
            for i, user_id in enumerate(list(all_user_ids)[:10], 1):
                # Count interactions for this user
                team_count = team_user_ids.count(user_id)
                contribution_count = contribution_user_ids.count(user_id)
                application_count = application_user_ids.count(user_id)
                total_interactions = team_count + contribution_count + application_count
                
                print(f"   {i}. {user_id} (interactions: {total_interactions})")
                print(f"      - Team: {team_count}, Contributions: {contribution_count}, Applications: {application_count}")
            
            if len(all_user_ids) > 10:
                print(f"   ... and {len(all_user_ids) - 10} more users")
            
            # Get the most active user
            most_active_user = max(all_user_ids, key=lambda uid: 
                team_user_ids.count(uid) + contribution_user_ids.count(uid) + application_user_ids.count(uid))
            
            print(f"\n🚀 Most active user for testing:")
            print(f"   User ID: {most_active_user}")
            print(f"   Total interactions: {team_user_ids.count(most_active_user) + contribution_user_ids.count(most_active_user) + application_user_ids.count(most_active_user)}")
            print(f"\n📝 Test command:")
            print(f"   curl -X GET \"http://localhost:8000/recommendations/{most_active_user}?top_n=5\"")
            
        else:
            print("❌ No users with interactions found!")
            
    finally:
        db.close()

if __name__ == "__main__":
    find_users_with_interactions() 