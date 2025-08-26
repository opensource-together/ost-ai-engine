import datetime
import uuid

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Text, UniqueConstraint)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base, relationship

# --- Base Class ---
Base = declarative_base()

# --- Association Tables (must be defined before main tables) ---

class ProjectTechStack(Base):
    """Association table for Project-TechStack many-to-many"""
    __tablename__ = "PROJECT_TECH_STACK"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    tech_stack_id = Column(UUID(as_uuid=True), ForeignKey("TECH_STACK.id"), primary_key=True)


class UserTechStack(Base):
    """Association table for User-TechStack many-to-many"""
    __tablename__ = "USER_TECH_STACK"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    tech_stack_id = Column(UUID(as_uuid=True), ForeignKey("TECH_STACK.id"), primary_key=True)


class ProjectCategory(Base):
    """Association table for Project-Category many-to-many"""
    __tablename__ = "PROJECT_CATEGORY"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("CATEGORY.id"), primary_key=True)


class UserCategory(Base):
    """Association table for User-Category many-to-many"""
    __tablename__ = "USER_CATEGORY"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("CATEGORY.id"), primary_key=True)


class ProjectRoleTechStack(Base):
    """Association table for ProjectRole-TechStack many-to-many"""
    __tablename__ = "PROJECT_ROLE_TECH_STACK"

    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), primary_key=True)
    tech_stack_id = Column(UUID(as_uuid=True), ForeignKey("TECH_STACK.id"), primary_key=True)


class TeamMemberProjectRole(Base):
    """Association table for TeamMember-ProjectRole many-to-many"""
    __tablename__ = "TEAM_MEMBER_PROJECT_ROLE"

    team_member_id = Column(UUID(as_uuid=True), ForeignKey("TEAM_MEMBER.id"), primary_key=True)
    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), primary_key=True)


class ProjectRoleApplicationKeyFeature(Base):
    """Association table for ProjectRoleApplication-KeyFeature many-to-many"""
    __tablename__ = "PROJECT_ROLE_APPLICATION_KEY_FEATURE"

    application_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE_APPLICATION.id"), primary_key=True)
    key_feature_id = Column(UUID(as_uuid=True), ForeignKey("KEY_FEATURE.id"), primary_key=True)


class ProjectRoleApplicationProjectGoal(Base):
    """Association table for ProjectRoleApplication-ProjectGoal many-to-many"""
    __tablename__ = "PROJECT_ROLE_APPLICATION_PROJECT_GOAL"

    application_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE_APPLICATION.id"), primary_key=True)
    key_feature_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_GOAL.id"), primary_key=True)


# --- Core Tables ---

class User(Base):
    __tablename__ = "USER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(30), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    login = Column(String(100))  # GitHub login
    avatar_url = Column(Text)  # GitHub avatar URL (mapped to avatarUrl in Prisma)
    location = Column(String(100))  # Max 100 characters
    company = Column(String(100))  # Company name
    bio = Column(Text)  # Max 500 characters
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    github_credentials = relationship("UserGitHubCredentials", back_populates="user", uselist=False)
    tech_stacks = relationship("TechStack", secondary=UserTechStack.__tablename__, back_populates="users")
    categories = relationship("Category", secondary=UserCategory.__tablename__, back_populates="users")
    social_links = relationship("UserSocialLink", back_populates="user")
    owned_projects = relationship("Project", foreign_keys="[Project.owner_id]", back_populates="owner")
    authored_projects = relationship("Project", foreign_keys="[Project.author_id]", back_populates="author")
    project_role_applications = relationship("ProjectRoleApplication", back_populates="user")


class UserGitHubCredentials(Base):
    __tablename__ = "USER_GITHUB_CREDENTIALS"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    github_access_token = Column(Text)
    github_user_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    user = relationship("User", back_populates="github_credentials")


class Project(Base):
    __tablename__ = "PROJECT"

    # --- Identifiers ---
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(
        String(150),
        unique=True,
        nullable=False,
        comment="Repository full name (e.g., 'owner/repo')",
    )

    # --- Core GitHub Fields ---
    title = Column(String(100), nullable=False)
    description = Column(Text)
    short_description = Column(Text)
    readme = Column(Text)
    primary_language = Column(String(50), comment="Primary programming language from GitHub")
    homepage_url = Column(Text)
    license = Column(String(100), comment="License SPDX ID from GitHub")

    # --- GitHub Stats ---
    stargazers_count = Column(Integer, default=0, nullable=False)
    watchers_count = Column(Integer, default=0, nullable=False)
    forks_count = Column(Integer, default=0, nullable=False)
    open_issues_count = Column(Integer, default=0, nullable=False)

    # --- Status Flags ---
    is_fork = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_disabled = Column(Boolean, default=False, nullable=False)

    # --- Rich Data Structures ---
    topics = Column(ARRAY(String), comment="List of repository topics from GitHub")
    languages = Column(
        JSONB, comment="JSON object of languages and their byte counts from GitHub"
    )

    # --- Timestamps ---
    created_at = Column(
        DateTime(timezone=True), comment="Timestamp of repository creation on GitHub"
    )
    updated_at = Column(DateTime(timezone=True), comment="Timestamp of last update on GitHub")
    pushed_at = Column(DateTime(timezone=True), comment="Timestamp of last push on GitHub")
    last_ingested_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        comment="Timestamp of when the record was last ingested or updated by our system",
    )

    # --- Internal Fields (may be manually populated or from other sources) ---
    image = Column(Text)
    cover_images = Column(Text)

    # --- Foreign Keys & Relationships ---
    author_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"))
    owner_login = Column(String(39), comment="GitHub owner's login, for reference")

    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    author = relationship("User", foreign_keys=[author_id], back_populates="authored_projects")
    external_links = relationship("ProjectExternalLink", back_populates="project")
    tech_stacks = relationship(
        "TechStack", secondary=ProjectTechStack.__tablename__, back_populates="projects"
    )
    project_members = relationship("TeamMember", back_populates="project")
    project_roles = relationship("ProjectRole", back_populates="project")
    categories = relationship(
        "Category", secondary=ProjectCategory.__tablename__, back_populates="projects"
    )
    key_features = relationship("KeyFeature", back_populates="project")
    project_goals = relationship("ProjectGoal", back_populates="project")
    project_role_applications = relationship(
        "ProjectRoleApplication", back_populates="project"
    )


class ProjectExternalLink(Base):
    __tablename__ = "PROJECT_EXTERNAL_LINK"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    type = Column(String(50))  # "github", "website", "documentation", etc.
    url = Column(Text, nullable=False)

    project = relationship("Project", back_populates="external_links")


class TechStack(Base):
    """Technologies and tools (React, Python, Figma, Docker, etc.)"""
    __tablename__ = "TECH_STACK"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # "React", "Python", "Figma", "Docker"
    icon_url = Column(Text)  # URL format (mapped to iconUrl in Prisma)
    type = Column(String(20))  # "LANGUAGE" or "TECH"
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Many-to-many relationships
    projects = relationship("Project", secondary=ProjectTechStack.__tablename__, back_populates="tech_stacks")
    project_roles = relationship("ProjectRole", secondary=ProjectRoleTechStack.__tablename__, back_populates="tech_stacks")
    users = relationship("User", secondary=UserTechStack.__tablename__, back_populates="tech_stacks")


class TeamMember(Base):
    __tablename__ = "TEAM_MEMBER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User")
    project = relationship("Project", back_populates="project_members")
    project_roles = relationship("ProjectRole", secondary=TeamMemberProjectRole.__tablename__, back_populates="team_members")


class ProjectRole(Base):
    __tablename__ = "PROJECT_ROLE"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    is_filled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    project = relationship("Project", back_populates="project_roles")
    tech_stacks = relationship("TechStack", secondary=ProjectRoleTechStack.__tablename__, back_populates="project_roles")
    team_members = relationship("TeamMember", secondary=TeamMemberProjectRole.__tablename__, back_populates="project_roles")
    applications = relationship("ProjectRoleApplication", back_populates="project_role")


class ProjectRoleApplication(Base):
    __tablename__ = "PROJECT_ROLE_APPLICATION"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    project_title = Column(String(100))  # Keep for history
    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), nullable=False)
    project_role_title = Column(String(100))  # Keep for history
    project_description = Column(Text)  # New field for project description
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)  # ADDED missing field
    status = Column(String(20))  # "pending", "accepted", "rejected", "withdrawn"
    motivation_letter = Column(Text)
    rejection_reason = Column(Text)
    applied_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    project_role = relationship("ProjectRole", back_populates="applications")
    user = relationship("User", back_populates="project_role_applications")
    project = relationship("Project", back_populates="project_role_applications")
    selected_key_features = relationship("KeyFeature", secondary=ProjectRoleApplicationKeyFeature.__tablename__, back_populates="applications")
    selected_project_goals = relationship("ProjectGoal", secondary=ProjectRoleApplicationProjectGoal.__tablename__, back_populates="applications")


class UserSocialLink(Base):
    __tablename__ = "USER_SOCIAL_LINK"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    type = Column(String(50))  # "github", "twitter", "linkedin", "website"
    url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="social_links")

    __table_args__ = (
        UniqueConstraint("user_id", "type", name="_user_social_link_uc"),
    )


class Category(Base):
    """Categories for projects (Education, Health, Finance, Gaming, etc.)"""
    __tablename__ = "CATEGORY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # "Education", "Finance", "Gaming", "DevTools"
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Many-to-many relationships
    projects = relationship("Project", secondary=ProjectCategory.__tablename__, back_populates="categories")
    users = relationship("User", secondary=UserCategory.__tablename__, back_populates="categories")


class KeyFeature(Base):
    """Key features of a project"""
    __tablename__ = "KEY_FEATURE"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    feature = Column(String(200), nullable=False)

    project = relationship("Project", back_populates="key_features")
    applications = relationship("ProjectRoleApplication", secondary=ProjectRoleApplicationKeyFeature.__tablename__, back_populates="selected_key_features")


class ProjectGoal(Base):
    """Goals of a project"""
    __tablename__ = "PROJECT_GOAL"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    goal = Column(String(200), nullable=False)

    project = relationship("Project", back_populates="project_goals")
    applications = relationship("ProjectRoleApplication", secondary=ProjectRoleApplicationProjectGoal.__tablename__, back_populates="selected_project_goals")


# =============================================================================
# 🧠 MACHINE LEARNING TABLES
# =============================================================================
# Tables dedicated to ML operations: embeddings, training data, and vector storage
# These tables support our hybrid recommendation system with TF-IDF and semantic search
# =============================================================================

# TrainingProject table removed - replaced by EmbedProjects for modern embedding-based recommendations


class EmbedProjects(Base):
    """Embedding data table for project recommendations with enriched text and pgvector storage"""
    __tablename__ = "embed_PROJECTS"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    embedding_text = Column(Text, nullable=False, comment="Enriched text for embedding generation")
    embedding_vector = Column(Vector(384), comment="384-dimensional embedding vector for similarity search")
    last_ingested_at = Column(DateTime(timezone=True), comment="Last data ingestion timestamp")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationship to original project
    project = relationship("Project")


class HybridProjectEmbeddings(Base):
    """Hybrid embedding table combining semantic embeddings with structured features for better User↔Project similarity"""
    __tablename__ = "hybrid_PROJECT_embeddings"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    semantic_embedding = Column(Vector(384), comment="384-dimensional semantic embedding from sentence-transformers")
    structured_features = Column(JSONB, comment="Structured features: categories, tech_stacks, language")
    hybrid_vector = Column(Vector(422), comment="422-dimensional hybrid vector: semantic(384) + structured(38)")
    similarity_weights = Column(JSONB, comment="Weights for different similarity components")
    last_ingested_at = Column(DateTime(timezone=True), comment="Last data ingestion timestamp")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationship to original project
    project = relationship("Project")


class EmbedUsers(Base):
    """Embedding data table for user recommendations with enriched text and pgvector storage"""
    __tablename__ = "embed_USERS"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    username = Column(String(255), nullable=False, comment="Username for reference")
    embedding_text = Column(Text, nullable=False, comment="Enriched text for embedding generation")
    embedding_vector = Column(Vector(384), comment="384-dimensional embedding vector for similarity search")
    bio = Column(Text, comment="Original user bio")
    categories = Column(ARRAY(String), comment="Array of category names")
    last_ingested_at = Column(DateTime(timezone=True), comment="Last data ingestion timestamp")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationship to original user
    user = relationship("User")
 