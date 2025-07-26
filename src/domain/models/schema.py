import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

# --- Base Class ---
Base = declarative_base()

# --- Core Tables ---


class User(Base):
    __tablename__ = "USER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(30), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    # New fields from MCD
    bio = Column(Text)  # Max 500 characters
    github_username = Column(String(39))  # Max 39 characters, unique if present
    linkedin_url = Column(Text)  # URL format
    github_url = Column(Text)  # URL format
    portfolio_url = Column(Text)  # URL format
    contribution_score = Column(Integer, default=0)  # ≥ 0, calculated automatically
    level = Column(String(20), default="beginner")  # "beginner", "intermediate", "advanced"
    is_open_to_hire = Column(Boolean, default=False)  # Open to contribution opportunities
    location = Column(String(100))  # Max 100 characters
    timezone = Column(String(50))  # IANA format (e.g., "Europe/Paris")
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships - Simplified to avoid SQLAlchemy conflicts
    team_memberships = relationship("TeamMember", back_populates="user")
    user_skills = relationship("UserSkill", back_populates="user")
    user_technologies = relationship("UserTechnology", back_populates="user")
    owned_projects = relationship("Project", back_populates="owner")
    community_memberships = relationship("CommunityMember", back_populates="user")


class Project(Base):
    __tablename__ = "PROJECT"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)  # Project owner
    title = Column(String(100), nullable=False)
    description = Column(Text)
    vision = Column(Text)  # Project vision from docs
    github_main_repo = Column(Text)  # Main GitHub repo URL
    website_url = Column(Text)  # Project website
    documentation_url = Column(Text)  # URL of the documentation
    difficulty = Column(String(20))  # "easy", "medium", "hard"
    status = Column(String(20), default="active")  # "active", "paused", "completed", "archived"
    is_seeking_contributors = Column(Boolean, default=True)
    project_type = Column(String(50))  # "library", "application", "tool", "framework", "other"
    license = Column(String(50))  # "MIT", "Apache-2.0", "GPL-3.0", "custom", "other"
    stars_count = Column(Integer, default=0)  # Renamed from stargazers_count
    contributors_count = Column(Integer, default=0)  # Number of active contributors
    language = Column(String(50))  # Primary programming language
    topics = Column(Text)  # Comma-separated topics
    # Legacy fields for compatibility with current data
    readme = Column(Text)
    forks_count = Column(Integer)
    open_issues_count = Column(Integer)
    pushed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationships
    owner = relationship("User", back_populates="owned_projects")
    roles = relationship("ProjectRole", back_populates="project")
    team_members = relationship("TeamMember", back_populates="project")
    contributions = relationship("Contribution", back_populates="project")
    issues = relationship("GoodFirstIssue", back_populates="project")
    linked_repositories = relationship("LinkedRepository", back_populates="project")
    project_skills = relationship("ProjectSkill", back_populates="project")
    project_technologies = relationship("ProjectTechnology", back_populates="project")
    project_domain_categories = relationship("ProjectDomainCategory", back_populates="project")
    community_members = relationship("CommunityMember", back_populates="project")


class ProjectTraining(Base):
    """
    Model for preprocessed project data used in ML training pipeline.
    This table contains cleaned and balanced data from the original PROJECT table.
    """
    __tablename__ = "PROJECT_training"

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)  # Contains combined cleaned text (title + description)
    vision = Column(Text)  # Project vision
    github_main_repo = Column(Text)  # Main GitHub repo URL
    website_url = Column(Text)  # Project website
    difficulty = Column(String(20))  # "easy", "medium", "hard"
    status = Column(String(20), default="active")
    is_seeking_contributors = Column(Boolean, default=True)
    project_type = Column(String(50))  # "web_app", "api", "cli", "mobile_app", "library"
    license = Column(String(50))  # License type
    stars_count = Column(Integer, default=0)  # Renamed from stargazers_count
    language = Column(String(50))  # Primary programming language
    topics = Column(Text)  # Comma-separated cleaned topics
    # Legacy fields for ML compatibility
    readme = Column(Text)
    forks_count = Column(Integer)
    open_issues_count = Column(Integer)
    pushed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class DomainCategory(Base):
    """Domain categories for projects (Education, Health, Finance, Gaming, etc.)"""
    __tablename__ = "DOMAIN_CATEGORY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # "Education", "Santé", "Finance", "Gaming", "DevTools"
    description = Column(Text)  # Max 500 characters
    icon_url = Column(Text)  # URL format
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    project_domain_categories = relationship("ProjectDomainCategory", back_populates="domain_category")


class Technology(Base):
    """Technologies and tools (React, Python, Figma, Docker, Slack, Notion, etc.)"""
    __tablename__ = "TECHNOLOGY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # "React", "Python", "Figma", "Docker", "Slack", "Notion"
    description = Column(Text)  # Max 500 characters
    icon_url = Column(Text)  # URL format
    category = Column(String(50))  # "frontend", "backend", "design", "devops", "business", "other"
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    user_technologies = relationship("UserTechnology", back_populates="technology")
    project_technologies = relationship("ProjectTechnology", back_populates="technology")
    project_role_technologies = relationship("ProjectRoleTechnology", back_populates="technology")
    issue_technologies = relationship("IssueTechnology", back_populates="technology")


class SkillCategory(Base):
    __tablename__ = "SKILL_CATEGORY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)  # "Frontend", "Backend", "Design", etc.
    description = Column(Text)  # Max 500 characters
    icon_url = Column(Text)  # URL format
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    skills = relationship("Skill", back_populates="category")


class Skill(Base):
    """Business skills (Product Management, Marketing, SEO, Community Management, etc.)"""
    __tablename__ = "SKILL"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_category_id = Column(UUID(as_uuid=True), ForeignKey("SKILL_CATEGORY.id"), nullable=False)
    name = Column(String(100), nullable=False, unique=True)  # "Product Management", "Marketing", "SEO", "Community Management"
    description = Column(Text)  # Max 500 characters
    icon_url = Column(Text)  # URL format
    is_technical = Column(Boolean, default=True)  # Technical skill or not
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    category = relationship("SkillCategory", back_populates="skills")
    user_skills = relationship("UserSkill", back_populates="skill")
    project_skills = relationship("ProjectSkill", back_populates="skill")
    project_role_skills = relationship("ProjectRoleSkill", back_populates="skill")
    issue_skills = relationship("IssueSkill", back_populates="skill")


class ProjectRole(Base):
    __tablename__ = "PROJECT_ROLE"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text)  # Max 1000 characters
    responsibility_level = Column(String(20))  # "contributor", "maintainer", "lead"
    time_commitment = Column(String(20))  # "few_hours", "part_time", "full_time"
    slots_available = Column(Integer, default=1)  # ≥ 0
    slots_filled = Column(Integer, default=0)  # Calculated automatically
    experience_required = Column(String(20))  # "none", "some", "experienced"
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="roles")
    applications = relationship("Application", back_populates="role")
    required_skills = relationship("ProjectRoleSkill", back_populates="project_role")
    required_technologies = relationship("ProjectRoleTechnology", back_populates="project_role")
    team_members = relationship("TeamMember", back_populates="project_role")


class TeamMember(Base):
    __tablename__ = "TEAM_MEMBER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), nullable=False)
    status = Column(String(20), default="active")  # "active", "inactive", "left"
    contributions_count = Column(Integer, default=0)  # Calculated automatically
    joined_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    left_at = Column(DateTime(timezone=True))  # Optional

    user = relationship("User", back_populates="team_memberships")
    project = relationship("Project", back_populates="team_members")
    project_role = relationship("ProjectRole", back_populates="team_members")

    __table_args__ = (
        UniqueConstraint('user_id', 'project_id', name='uq_team_member'),
    )


class Contribution(Base):
    __tablename__ = "CONTRIBUTION"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("GOOD_FIRST_ISSUE.id"))  # Optional
    type = Column(String(50))  # "code", "design", "documentation", "bug_fix", "feature", "other"
    title = Column(String(200), nullable=False)  # Max 200 characters
    description = Column(Text)  # Max 1000 characters
    github_pr_url = Column(Text)  # URL format
    status = Column(String(20), default="submitted")  # "submitted", "reviewed", "merged", "rejected"
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("USER.id"))  # Optional
    submitted_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    merged_at = Column(DateTime(timezone=True))  # Optional

    # Relationships - Simplified to avoid SQLAlchemy conflicts
    project = relationship("Project", back_populates="contributions")
    issue = relationship("GoodFirstIssue", back_populates="contributions")


class Application(Base):
    __tablename__ = "APPLICATION"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_role_id = Column(
        UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), nullable=False
    )
    portfolio_links = Column(Text)  # JSON array of URLs
    availability = Column(String(20))  # "immediate", "within_week", "within_month"
    status = Column(String(20), default="pending")  # "pending", "accepted", "rejected", "withdrawn"
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("USER.id"))  # Optional
    review_message = Column(Text)  # Max 500 characters
    applied_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    reviewed_at = Column(DateTime(timezone=True))  # Optional

    # Relationships - Simplified to avoid SQLAlchemy conflicts
    role = relationship("ProjectRole", back_populates="applications")

    __table_args__ = (
        UniqueConstraint("user_id", "project_role_id", name="_user_project_role_uc"),
    )


class UserSkill(Base):
    __tablename__ = "USER_SKILL"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("SKILL.id"), nullable=False)
    proficiency_level = Column(String(20), nullable=False)  # "learning", "basic", "intermediate", "advanced", "expert"
    is_primary = Column(Boolean, default=False)  # Primary skill or not
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="_user_skill_uc"),
    )


class UserTechnology(Base):
    """User's technology proficiency"""
    __tablename__ = "USER_TECHNOLOGY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    technology_id = Column(UUID(as_uuid=True), ForeignKey("TECHNOLOGY.id"), nullable=False)
    proficiency_level = Column(String(20), nullable=False)  # "learning", "basic", "intermediate", "advanced", "expert"
    is_primary = Column(Boolean, default=False)  # Primary technology or not
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="user_technologies")
    technology = relationship("Technology", back_populates="user_technologies")

    __table_args__ = (
        UniqueConstraint("user_id", "technology_id", name="_user_technology_uc"),
    )


class ProjectDomainCategory(Base):
    """Project's domain categories"""
    __tablename__ = "PROJECT_DOMAIN_CATEGORY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    domain_category_id = Column(UUID(as_uuid=True), ForeignKey("DOMAIN_CATEGORY.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # Primary domain category

    project = relationship("Project", back_populates="project_domain_categories")
    domain_category = relationship("DomainCategory", back_populates="project_domain_categories")

    __table_args__ = (
        UniqueConstraint("project_id", "domain_category_id", name="_project_domain_category_uc"),
    )


class ProjectSkill(Base):
    """Skills used by a project"""
    __tablename__ = "PROJECT_SKILL"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("SKILL.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # Primary skill for the project

    project = relationship("Project", back_populates="project_skills")
    skill = relationship("Skill", back_populates="project_skills")

    __table_args__ = (
        UniqueConstraint("project_id", "skill_id", name="_project_skill_uc"),
    )


class ProjectTechnology(Base):
    """Technologies used by a project"""
    __tablename__ = "PROJECT_TECHNOLOGY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    technology_id = Column(UUID(as_uuid=True), ForeignKey("TECHNOLOGY.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # Primary technology for the project

    project = relationship("Project", back_populates="project_technologies")
    technology = relationship("Technology", back_populates="project_technologies")

    __table_args__ = (
        UniqueConstraint("project_id", "technology_id", name="_project_technology_uc"),
    )


class ProjectRoleSkill(Base):
    __tablename__ = "PROJECT_ROLE_SKILL"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("SKILL.id"), nullable=False)
    proficiency_level = Column(String(20), nullable=False)  # "basic", "intermediate", "advanced"
    is_required = Column(Boolean, default=True)  # Required or optional skill

    project_role = relationship("ProjectRole", back_populates="required_skills")
    skill = relationship("Skill", back_populates="project_role_skills")

    __table_args__ = (
        UniqueConstraint("project_role_id", "skill_id", name="_project_role_skill_uc"),
    )


class ProjectRoleTechnology(Base):
    """Technologies required for a project role"""
    __tablename__ = "PROJECT_ROLE_TECHNOLOGY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), nullable=False)
    technology_id = Column(UUID(as_uuid=True), ForeignKey("TECHNOLOGY.id"), nullable=False)
    proficiency_level = Column(String(20), nullable=False)  # "basic", "intermediate", "advanced"
    is_required = Column(Boolean, default=True)  # Required or optional technology

    project_role = relationship("ProjectRole", back_populates="required_technologies")
    technology = relationship("Technology", back_populates="project_role_technologies")

    __table_args__ = (
        UniqueConstraint("project_role_id", "technology_id", name="_project_role_technology_uc"),
    )


class GoodFirstIssue(Base):
    __tablename__ = "GOOD_FIRST_ISSUE"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    title = Column(String(200), nullable=False)  # Max 200 characters
    description = Column(Text)  # Max 2000 characters
    github_issue_url = Column(Text)  # URL format
    estimated_time = Column(String(20))  # "30min", "1h", "2h", "4h", "1day"
    difficulty = Column(String(20))  # "very_easy", "easy", "medium"
    status = Column(String(20), default="open")  # "open", "assigned", "in_progress", "completed", "closed"
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("USER.id"))  # Optional
    is_ai_generated = Column(Boolean, default=False)  # AI-generated issue
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))  # Optional

    project = relationship("Project", back_populates="issues")
    # Relationships - Simplified to avoid SQLAlchemy conflicts
    issue_skills = relationship("IssueSkill", back_populates="issue")
    issue_technologies = relationship("IssueTechnology", back_populates="issue")
    contributions = relationship("Contribution", back_populates="issue")


class IssueSkill(Base):
    __tablename__ = "ISSUE_SKILL"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("GOOD_FIRST_ISSUE.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("SKILL.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # Primary skill for the issue

    issue = relationship("GoodFirstIssue", back_populates="issue_skills")
    skill = relationship("Skill", back_populates="issue_skills")

    __table_args__ = (
        UniqueConstraint("issue_id", "skill_id", name="_issue_skill_uc"),
    )


class IssueTechnology(Base):
    """Technologies needed for an issue"""
    __tablename__ = "ISSUE_TECHNOLOGY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("GOOD_FIRST_ISSUE.id"), nullable=False)
    technology_id = Column(UUID(as_uuid=True), ForeignKey("TECHNOLOGY.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # Primary technology for the issue

    issue = relationship("GoodFirstIssue", back_populates="issue_technologies")
    technology = relationship("Technology", back_populates="issue_technologies")

    __table_args__ = (
        UniqueConstraint("issue_id", "technology_id", name="_issue_technology_uc"),
    )


class CommunityMember(Base):
    """Users following projects as community members"""
    __tablename__ = "COMMUNITY_MEMBER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    followed_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    notifications_enabled = Column(Boolean, default=True)  # Enable notifications for this project

    user = relationship("User", back_populates="community_memberships")
    project = relationship("Project", back_populates="community_members")

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="_community_member_uc"),
    )


class LinkedRepository(Base):
    __tablename__ = "LINKED_REPOSITORY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    github_url = Column(Text, nullable=False)  # GitHub URL
    name = Column(String(100), nullable=False)  # Max 100 characters
    description = Column(Text)  # Max 500 characters
    is_main = Column(Boolean, default=False)  # Main repository of the project
    language = Column(String(50))  # "JavaScript", "Python", etc.
    stars_count = Column(Integer, default=0)  # ≥ 0, synchronized
    last_sync = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="linked_repositories")

    __table_args__ = (
        UniqueConstraint("project_id", "github_url", name="_linked_repository_uc"),
    )
 