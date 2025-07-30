#!/usr/bin/env python3
"""
Reference Data Population Script

This script populates the database with reference data:
- TECH_STACK (unified skills and technologies)
- CATEGORY (project categories)

This data is required by scraping.py and simulate_users.py.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session

from src.domain.models.schema import (
    TechStack,
    Category,
)
from src.infrastructure.logger import log
from src.infrastructure.postgres.database import SessionLocal


class ReferenceDataPopulator:
    """Handles population of reference data (tech stacks, categories)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def populate_all_reference_data(self):
        """Populate all reference data."""
        log.info("🚀 Starting reference data population...")
        
        # Clear existing reference data
        self._clear_existing_reference_data()
        
        # Populate in correct order
        self._populate_tech_stacks()
        self._populate_categories()
        
        log.info("🎉 Reference data population completed!")
        self._log_statistics()
    
    def _clear_existing_reference_data(self):
        """Clear existing reference data in correct order."""
        log.info("Clearing existing reference data...")
        
        # Delete in order to respect foreign key constraints
        self.db.query(TechStack).delete()
        self.db.query(Category).delete()
        self.db.commit()
        
        log.info("✅ Cleared existing reference data")
    
    def _populate_tech_stacks(self):
        """Populate tech stacks (unified skills and technologies)."""
        log.info("Creating tech stacks...")
        
        tech_stacks = [
            # Frontend Technologies
            TechStack(name="React", icon_url="https://example.com/icons/react.png", type="TECH"),
            TechStack(name="Vue.js", icon_url="https://example.com/icons/vue.png", type="TECH"),
            TechStack(name="TypeScript", icon_url="https://example.com/icons/typescript.png", type="LANGUAGE"),
            TechStack(name="CSS", icon_url="https://example.com/icons/css.png", type="TECH"),
            TechStack(name="HTML", icon_url="https://example.com/icons/html.png", type="LANGUAGE"),
            TechStack(name="Figma", icon_url="https://example.com/icons/figma.png", type="TECH"),
            
            # Backend Technologies
            TechStack(name="Python", icon_url="https://example.com/icons/python.png", type="LANGUAGE"),
            TechStack(name="Node.js", icon_url="https://example.com/icons/nodejs.png", type="TECH"),
            TechStack(name="Java", icon_url="https://example.com/icons/java.png", type="LANGUAGE"),
            TechStack(name="Go", icon_url="https://example.com/icons/go.png", type="LANGUAGE"),
            TechStack(name="PostgreSQL", icon_url="https://example.com/icons/postgresql.png", type="TECH"),
            TechStack(name="Docker", icon_url="https://example.com/icons/docker.png", type="TECH"),
            TechStack(name="Kubernetes", icon_url="https://example.com/icons/kubernetes.png", type="TECH"),
            TechStack(name="AWS", icon_url="https://example.com/icons/aws.png", type="TECH"),
            TechStack(name="Git", icon_url="https://example.com/icons/git.png", type="TECH"),
            TechStack(name="GitHub", icon_url="https://example.com/icons/github.png", type="TECH"),
            
            # Mobile Technologies
            TechStack(name="React Native", icon_url="https://example.com/icons/react-native.png", type="TECH"),
            TechStack(name="Flutter", icon_url="https://example.com/icons/flutter.png", type="TECH"),
            TechStack(name="Xcode", icon_url="https://example.com/icons/xcode.png", type="TECH"),
            TechStack(name="Android Studio", icon_url="https://example.com/icons/android-studio.png", type="TECH"),
            
            # Data Technologies
            TechStack(name="Pandas", icon_url="https://example.com/icons/pandas.png", type="TECH"),
            
            # Additional Technologies
            TechStack(name="Rust", icon_url="https://example.com/icons/rust.png", type="LANGUAGE"),
            TechStack(name="C#", icon_url="https://example.com/icons/csharp.png", type="LANGUAGE"),
            TechStack(name=".NET", icon_url="https://example.com/icons/dotnet.png", type="TECH"),
            TechStack(name="Visual Studio", icon_url="https://example.com/icons/visual-studio.png", type="TECH"),
            TechStack(name="PHP", icon_url="https://example.com/icons/php.png", type="LANGUAGE"),
            TechStack(name="Laravel", icon_url="https://example.com/icons/laravel.png", type="TECH"),
            TechStack(name="MySQL", icon_url="https://example.com/icons/mysql.png", type="TECH"),
            TechStack(name="Ruby", icon_url="https://example.com/icons/ruby.png", type="LANGUAGE"),
            TechStack(name="Ruby on Rails", icon_url="https://example.com/icons/rails.png", type="TECH"),
            TechStack(name="Swift", icon_url="https://example.com/icons/swift.png", type="LANGUAGE"),
            TechStack(name="Kotlin", icon_url="https://example.com/icons/kotlin.png", type="LANGUAGE"),
            TechStack(name="Scala", icon_url="https://example.com/icons/scala.png", type="LANGUAGE"),
            TechStack(name="Spark", icon_url="https://example.com/icons/spark.png", type="TECH"),
            TechStack(name="C++", icon_url="https://example.com/icons/cpp.png", type="LANGUAGE"),
            TechStack(name="C", icon_url="https://example.com/icons/c.png", type="LANGUAGE"),
            TechStack(name="Linux", icon_url="https://example.com/icons/linux.png", type="TECH"),
            TechStack(name="Spring Boot", icon_url="https://example.com/icons/spring-boot.png", type="TECH"),
            TechStack(name="Maven", icon_url="https://example.com/icons/maven.png", type="TECH"),
            TechStack(name="ASP.NET Core", icon_url="https://example.com/icons/aspnet-core.png", type="TECH"),
            TechStack(name="Entity Framework", icon_url="https://example.com/icons/entity-framework.png", type="TECH"),
            TechStack(name="LINQ", icon_url="https://example.com/icons/linq.png", type="TECH"),
            TechStack(name="Gin", icon_url="https://example.com/icons/gin.png", type="TECH"),
            TechStack(name="Echo", icon_url="https://example.com/icons/echo.png", type="TECH"),
            TechStack(name="Microservices", icon_url="https://example.com/icons/microservices.png", type="TECH"),
            TechStack(name="WebAssembly", icon_url="https://example.com/icons/webassembly.png", type="TECH"),
            TechStack(name="Cargo", icon_url="https://example.com/icons/cargo.png", type="TECH"),
            TechStack(name="Crates.io", icon_url="https://example.com/icons/crates.png", type="TECH"),
            TechStack(name="UIKit", icon_url="https://example.com/icons/uikit.png", type="TECH"),
            TechStack(name="SwiftUI", icon_url="https://example.com/icons/swiftui.png", type="TECH"),
            TechStack(name="Akka", icon_url="https://example.com/icons/akka.png", type="TECH"),
            TechStack(name="Play Framework", icon_url="https://example.com/icons/play.png", type="TECH"),
        ]
        
        self.db.add_all(tech_stacks)
        self.db.commit()
        
        log.info(f"✅ Created {len(tech_stacks)} tech stacks")
        return tech_stacks
    
    def _populate_categories(self):
        """Populate project categories."""
        log.info("Creating project categories...")
        
        categories = [
            Category(name="Education"),
            Category(name="E-commerce"),
            Category(name="Social"),
            Category(name="Productivity"),
            Category(name="Entertainment"),
            Category(name="Finance"),
            Category(name="DevTools"),
            Category(name="Infrastructure"),
            Category(name="Microservices"),
            Category(name="Cloud"),
            Category(name="Systems Programming"),
            Category(name="Performance"),
            Category(name="Security"),
            Category(name="Embedded"),
            Category(name="Enterprise"),
            Category(name="Gaming"),
            Category(name="Healthcare"),
            Category(name="Government"),
            Category(name="Mobile Development"),
            Category(name="iOS"),
            Category(name="Apple Ecosystem"),
            Category(name="Android"),
            Category(name="Big Data"),
            Category(name="Analytics"),
            Category(name="High Performance"),
            Category(name="AI/ML"),
            Category(name="Web Development"),
        ]
        
        self.db.add_all(categories)
        self.db.commit()
        
        log.info(f"✅ Created {len(categories)} categories")
        return categories
    
    def _log_statistics(self):
        """Log final statistics."""
        log.info("📊 Reference Data Statistics:")
        log.info(f"   Tech Stacks: {self.db.query(TechStack).count()}")
        log.info(f"   Categories: {self.db.query(Category).count()}")


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