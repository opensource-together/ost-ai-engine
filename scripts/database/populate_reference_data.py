#!/usr/bin/env python3
"""
Reference Data Population Script

This script populates the database with reference data:
- SKILL_CATEGORY and SKILL
- TECHNOLOGY  
- DOMAIN_CATEGORY

This data is required by scraping.py and simulate_users.py.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session

from src.domain.models.schema import (
    SkillCategory,
    Skill,
    Technology,
    DomainCategory,
)
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import SessionLocal


class ReferenceDataPopulator:
    """Handles population of reference data (skills, technologies, domains)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def populate_all_reference_data(self):
        """Populate all reference data."""
        log.info("🚀 Starting reference data population...")
        
        # Clear existing reference data
        self._clear_existing_reference_data()
        
        # Populate in correct order
        self._populate_skill_categories()
        self._populate_skills()
        self._populate_technologies()
        self._populate_domain_categories()
        
        log.info("🎉 Reference data population completed!")
        self._log_statistics()
    
    def _clear_existing_reference_data(self):
        """Clear existing reference data in correct order."""
        log.info("Clearing existing reference data...")
        
        # Delete in order to respect foreign key constraints
        self.db.query(Skill).delete()
        self.db.query(SkillCategory).delete()
        self.db.query(Technology).delete()
        self.db.query(DomainCategory).delete()
        self.db.commit()
        
        log.info("✅ Cleared existing reference data")
    
    def _populate_skill_categories(self):
        """Populate skill categories."""
        log.info("Creating skill categories...")
        
        categories = [
            SkillCategory(
                name="Frontend Development",
                description="Skills related to frontend development and user interface",
                icon_url="https://example.com/icons/frontend.png"
            ),
            SkillCategory(
                name="Backend Development", 
                description="Skills related to backend development and server-side logic",
                icon_url="https://example.com/icons/backend.png"
            ),
            SkillCategory(
                name="Mobile Development",
                description="Skills related to mobile app development",
                icon_url="https://example.com/icons/mobile.png"
            ),
            SkillCategory(
                name="Data Science",
                description="Skills related to data analysis and machine learning",
                icon_url="https://example.com/icons/data.png"
            ),
            SkillCategory(
                name="DevOps",
                description="Skills related to infrastructure and deployment",
                icon_url="https://example.com/icons/devops.png"
            ),
            SkillCategory(
                name="Design",
                description="Skills related to UI/UX design and user experience",
                icon_url="https://example.com/icons/design.png"
            ),
            SkillCategory(
                name="Business",
                description="Skills related to business and product management",
                icon_url="https://example.com/icons/business.png"
            )
        ]
        
        self.db.add_all(categories)
        self.db.commit()
        
        log.info(f"✅ Created {len(categories)} skill categories")
        return categories
    
    def _populate_skills(self):
        """Populate skills with their categories."""
        log.info("Creating skills...")
        
        # Get skill categories
        frontend_cat = self.db.query(SkillCategory).filter_by(name="Frontend Development").first()
        backend_cat = self.db.query(SkillCategory).filter_by(name="Backend Development").first()
        mobile_cat = self.db.query(SkillCategory).filter_by(name="Mobile Development").first()
        data_cat = self.db.query(SkillCategory).filter_by(name="Data Science").first()
        devops_cat = self.db.query(SkillCategory).filter_by(name="DevOps").first()
        design_cat = self.db.query(SkillCategory).filter_by(name="Design").first()
        business_cat = self.db.query(SkillCategory).filter_by(name="Business").first()
        
        skills = [
            # Frontend Skills
            Skill(skill_category_id=frontend_cat.id, name="React", description="React.js framework", is_technical=True),
            Skill(skill_category_id=frontend_cat.id, name="Vue.js", description="Vue.js framework", is_technical=True),
            Skill(skill_category_id=frontend_cat.id, name="TypeScript", description="TypeScript language", is_technical=True),
            Skill(skill_category_id=frontend_cat.id, name="CSS", description="CSS styling", is_technical=True),
            Skill(skill_category_id=frontend_cat.id, name="HTML", description="HTML markup", is_technical=True),
            Skill(skill_category_id=frontend_cat.id, name="UI Design", description="User interface design", is_technical=False),
            
            # Backend Skills
            Skill(skill_category_id=backend_cat.id, name="Python", description="Python programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Node.js", description="Node.js runtime", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Java", description="Java programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Go", description="Go programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="API Design", description="API design and development", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Database Design", description="Database design and optimization", is_technical=True),
            
            # Mobile Skills
            Skill(skill_category_id=mobile_cat.id, name="React Native", description="React Native development", is_technical=True),
            Skill(skill_category_id=mobile_cat.id, name="Flutter", description="Flutter development", is_technical=True),
            Skill(skill_category_id=mobile_cat.id, name="iOS Development", description="iOS app development", is_technical=True),
            Skill(skill_category_id=mobile_cat.id, name="Android Development", description="Android app development", is_technical=True),
            Skill(skill_category_id=mobile_cat.id, name="Mobile Development", description="Mobile app development", is_technical=True),
            
            # Data Science Skills
            Skill(skill_category_id=data_cat.id, name="Machine Learning", description="Machine learning algorithms", is_technical=True),
            Skill(skill_category_id=data_cat.id, name="Data Analysis", description="Data analysis and visualization", is_technical=True),
            Skill(skill_category_id=data_cat.id, name="SQL", description="SQL database queries", is_technical=True),
            Skill(skill_category_id=data_cat.id, name="Pandas", description="Pandas data manipulation", is_technical=True),
            
            # DevOps Skills
            Skill(skill_category_id=devops_cat.id, name="Docker", description="Containerization with Docker", is_technical=True),
            Skill(skill_category_id=devops_cat.id, name="Kubernetes", description="Container orchestration", is_technical=True),
            Skill(skill_category_id=devops_cat.id, name="AWS", description="Amazon Web Services", is_technical=True),
            Skill(skill_category_id=devops_cat.id, name="CI/CD", description="Continuous integration/deployment", is_technical=True),
            Skill(skill_category_id=devops_cat.id, name="Linux", description="Linux system administration", is_technical=True),
            Skill(skill_category_id=devops_cat.id, name="Security", description="Cybersecurity practices", is_technical=True),
            
            # Design Skills
            Skill(skill_category_id=design_cat.id, name="UX Design", description="User experience design", is_technical=False),
            Skill(skill_category_id=design_cat.id, name="UI Design", description="User interface design", is_technical=False),
            Skill(skill_category_id=design_cat.id, name="Figma", description="Figma design tool", is_technical=True),
            
            # Business Skills
            Skill(skill_category_id=business_cat.id, name="Product Management", description="Product management and strategy", is_technical=False),
            Skill(skill_category_id=business_cat.id, name="Marketing", description="Digital marketing", is_technical=False),
            Skill(skill_category_id=business_cat.id, name="SEO", description="Search engine optimization", is_technical=False),
            Skill(skill_category_id=business_cat.id, name="Community Management", description="Community building and management", is_technical=False),
            
            # Additional Technical Skills
            Skill(skill_category_id=backend_cat.id, name="Rust", description="Rust programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="C#", description="C# programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="PHP", description="PHP programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Ruby", description="Ruby programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Swift", description="Swift programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Kotlin", description="Kotlin programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Scala", description="Scala programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="C++", description="C++ programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="C", description="C programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Systems Programming", description="Low-level systems programming", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Functional Programming", description="Functional programming paradigms", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Big Data", description="Big data processing", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Game Development", description="Game development", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Embedded", description="Embedded systems development", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="Performance", description="Performance optimization", is_technical=True),
            Skill(skill_category_id=backend_cat.id, name="WebAssembly", description="WebAssembly development", is_technical=True),
        ]
        
        self.db.add_all(skills)
        self.db.commit()
        
        log.info(f"✅ Created {len(skills)} skills")
        return skills
    
    def _populate_technologies(self):
        """Populate technologies."""
        log.info("Creating technologies...")
        
        technologies = [
            # Frontend Technologies
            Technology(name="React", description="React.js library", category="frontend"),
            Technology(name="Vue.js", description="Vue.js framework", category="frontend"),
            Technology(name="TypeScript", description="TypeScript language", category="frontend"),
            Technology(name="CSS", description="CSS styling", category="frontend"),
            Technology(name="HTML", description="HTML markup", category="frontend"),
            Technology(name="Figma", description="Figma design tool", category="design"),
            
            # Backend Technologies
            Technology(name="Python", description="Python programming language", category="backend"),
            Technology(name="Node.js", description="Node.js runtime", category="backend"),
            Technology(name="Java", description="Java programming language", category="backend"),
            Technology(name="Go", description="Go programming language", category="backend"),
            Technology(name="PostgreSQL", description="PostgreSQL database", category="backend"),
            Technology(name="Docker", description="Containerization platform", category="devops"),
            Technology(name="Kubernetes", description="Container orchestration", category="devops"),
            Technology(name="AWS", description="Amazon Web Services", category="devops"),
            Technology(name="Git", description="Version control system", category="devops"),
            Technology(name="GitHub", description="Git hosting platform", category="devops"),
            
            # Mobile Technologies
            Technology(name="React Native", description="React Native framework", category="mobile"),
            Technology(name="Flutter", description="Flutter framework", category="mobile"),
            Technology(name="Xcode", description="iOS development IDE", category="mobile"),
            Technology(name="Android Studio", description="Android development IDE", category="mobile"),
            
            # Data Technologies
            Technology(name="Pandas", description="Python data analysis library", category="data"),
            Technology(name="PostgreSQL", description="PostgreSQL database", category="data"),
            
            # Additional Technologies
            Technology(name="Rust", description="Rust programming language", category="backend"),
            Technology(name="C#", description="C# programming language", category="backend"),
            Technology(name=".NET", description=".NET framework", category="backend"),
            Technology(name="Visual Studio", description="Microsoft IDE", category="backend"),
            Technology(name="PHP", description="PHP programming language", category="backend"),
            Technology(name="Laravel", description="PHP framework", category="backend"),
            Technology(name="MySQL", description="MySQL database", category="backend"),
            Technology(name="Ruby", description="Ruby programming language", category="backend"),
            Technology(name="Ruby on Rails", description="Ruby web framework", category="backend"),
            Technology(name="Swift", description="Swift programming language", category="mobile"),
            Technology(name="Kotlin", description="Kotlin programming language", category="mobile"),
            Technology(name="Scala", description="Scala programming language", category="backend"),
            Technology(name="Spark", description="Apache Spark", category="data"),
            Technology(name="C++", description="C++ programming language", category="backend"),
            Technology(name="C", description="C programming language", category="backend"),
            Technology(name="Linux", description="Linux operating system", category="devops"),
            Technology(name="Spring Boot", description="Java framework", category="backend"),
            Technology(name="Maven", description="Java build tool", category="backend"),
            Technology(name="ASP.NET Core", description=".NET web framework", category="backend"),
            Technology(name="Entity Framework", description=".NET ORM", category="backend"),
            Technology(name="LINQ", description=".NET query language", category="backend"),
            Technology(name="Gin", description="Go web framework", category="backend"),
            Technology(name="Echo", description="Go web framework", category="backend"),
            Technology(name="Microservices", description="Microservices architecture", category="backend"),
            Technology(name="WebAssembly", description="WebAssembly runtime", category="frontend"),
            Technology(name="Cargo", description="Rust package manager", category="backend"),
            Technology(name="Crates.io", description="Rust package registry", category="backend"),
            Technology(name="UIKit", description="iOS UI framework", category="mobile"),
            Technology(name="SwiftUI", description="iOS UI framework", category="mobile"),
            Technology(name="Akka", description="Scala actor framework", category="backend"),
            Technology(name="Play Framework", description="Scala web framework", category="backend"),
        ]
        
        self.db.add_all(technologies)
        self.db.commit()
        
        log.info(f"✅ Created {len(technologies)} technologies")
        return technologies
    
    def _populate_domain_categories(self):
        """Populate domain categories."""
        log.info("Creating domain categories...")
        
        domains = [
            DomainCategory(name="Education", description="Educational and learning platforms"),
            DomainCategory(name="E-commerce", description="Online shopping and retail"),
            DomainCategory(name="Social", description="Social networking and communication"),
            DomainCategory(name="Productivity", description="Productivity and business tools"),
            DomainCategory(name="Entertainment", description="Gaming and entertainment"),
            DomainCategory(name="Finance", description="Financial services and fintech"),
            DomainCategory(name="DevTools", description="Developer tools and utilities"),
            DomainCategory(name="Infrastructure", description="Infrastructure and cloud services"),
            DomainCategory(name="Microservices", description="Microservices architecture"),
            DomainCategory(name="Cloud", description="Cloud computing and services"),
            DomainCategory(name="Systems Programming", description="Low-level systems development"),
            DomainCategory(name="Performance", description="Performance optimization tools"),
            DomainCategory(name="Security", description="Cybersecurity and privacy"),
            DomainCategory(name="Embedded", description="Embedded systems and IoT"),
            DomainCategory(name="Enterprise", description="Enterprise software solutions"),
            DomainCategory(name="Gaming", description="Game development and gaming"),
            DomainCategory(name="Healthcare", description="Healthcare and medical software"),
            DomainCategory(name="Government", description="Government and public sector"),
            DomainCategory(name="Mobile Development", description="Mobile app development"),
            DomainCategory(name="iOS", description="Apple iOS ecosystem"),
            DomainCategory(name="Apple Ecosystem", description="Apple platform development"),
            DomainCategory(name="Android", description="Google Android ecosystem"),
            DomainCategory(name="Big Data", description="Big data processing and analytics"),
            DomainCategory(name="Analytics", description="Data analytics and business intelligence"),
            DomainCategory(name="High Performance", description="High-performance computing"),
            DomainCategory(name="AI/ML", description="Artificial intelligence and machine learning"),
            DomainCategory(name="Web Development", description="Web application development"),
        ]
        
        self.db.add_all(domains)
        self.db.commit()
        
        log.info(f"✅ Created {len(domains)} domain categories")
        return domains
    
    def _log_statistics(self):
        """Log final statistics."""
        log.info("📊 Reference Data Statistics:")
        log.info(f"   Skill Categories: {self.db.query(SkillCategory).count()}")
        log.info(f"   Skills: {self.db.query(Skill).count()}")
        log.info(f"   Technologies: {self.db.query(Technology).count()}")
        log.info(f"   Domain Categories: {self.db.query(DomainCategory).count()}")


def main():
    """Main function to run the reference data population."""
    log.info("🚀 Starting reference data population...")
    
    db_session = SessionLocal()
    try:
        populator = ReferenceDataPopulator(db_session)
        populator.populate_all_reference_data()
    finally:
        db_session.close()
        log.info("Script finished. Database session closed.")


if __name__ == "__main__":
    main() 