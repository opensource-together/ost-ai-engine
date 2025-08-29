import datetime
import uuid

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Text, UniqueConstraint, Float, Index)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ProjectTechStack(Base):
    __tablename__ = "PROJECT_TECH_STACK"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    tech_stack_id = Column(UUID(as_uuid=True), ForeignKey("TECH_STACK.id"), primary_key=True)


class UserTechStack(Base):
    __tablename__ = "USER_TECH_STACK"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    tech_stack_id = Column(UUID(as_uuid=True), ForeignKey("TECH_STACK.id"), primary_key=True)


class ProjectCategory(Base):
    __tablename__ = "PROJECT_CATEGORY"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("CATEGORY.id"), primary_key=True)


class UserCategory(Base):
    __tablename__ = "USER_CATEGORY"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("CATEGORY.id"), primary_key=True)


class ProjectRoleTechStack(Base):
    __tablename__ = "PROJECT_ROLE_TECH_STACK"

    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), primary_key=True)
    tech_stack_id = Column(UUID(as_uuid=True), ForeignKey("TECH_STACK.id"), primary_key=True)


class TeamMemberProjectRole(Base):
    __tablename__ = "TEAM_MEMBER_PROJECT_ROLE"

    team_member_id = Column(UUID(as_uuid=True), ForeignKey("TEAM_MEMBER.id"), primary_key=True)
    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), primary_key=True)


class ProjectRoleApplicationKeyFeature(Base):
    __tablename__ = "PROJECT_ROLE_APPLICATION_KEY_FEATURE"

    application_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE_APPLICATION.id"), primary_key=True)
    key_feature_id = Column(UUID(as_uuid=True), ForeignKey("KEY_FEATURE.id"), primary_key=True)


class ProjectRoleApplicationProjectGoal(Base):
    __tablename__ = "PROJECT_ROLE_APPLICATION_PROJECT_GOAL"

    application_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE_APPLICATION.id"), primary_key=True)
    key_feature_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_GOAL.id"), primary_key=True)


class User(Base):
    __tablename__ = "USER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(30), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    login = Column(String(100))
    avatar_url = Column(Text)
    location = Column(String(100))
    company = Column(String(100))
    bio = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(
        String(150),
        unique=True,
        nullable=False,
    )

    title = Column(String(100), nullable=False)
    description = Column(Text)
    short_description = Column(Text)
    readme = Column(Text)
    primary_language = Column(String(50))
    homepage_url = Column(Text)
    license = Column(String(100))

    stargazers_count = Column(Integer, default=0, nullable=False)
    watchers_count = Column(Integer, default=0, nullable=False)
    forks_count = Column(Integer, default=0, nullable=False)
    open_issues_count = Column(Integer, default=0, nullable=False)

    is_fork = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_disabled = Column(Boolean, default=False, nullable=False)

    topics = Column(ARRAY(String))
    languages = Column(JSONB)

    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    pushed_at = Column(DateTime(timezone=True))
    last_ingested_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    image = Column(Text)
    cover_images = Column(Text)

    author_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"))
    owner_login = Column(String(39))

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
    type = Column(String(50))
    url = Column(Text, nullable=False)

    project = relationship("Project", back_populates="external_links")


class TechStack(Base):
    __tablename__ = "TECH_STACK"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    icon_url = Column(Text)
    type = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    projects = relationship("Project", secondary=ProjectTechStack.__tablename__, back_populates="tech_stacks")
    project_roles = relationship("ProjectRole", secondary=ProjectRoleTechStack.__tablename__, back_populates="tech_stacks")
    users = relationship("User", secondary=UserTechStack.__tablename__, back_populates="tech_stacks")


class TeamMember(Base):
    __tablename__ = "TEAM_MEMBER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

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

    project = relationship("Project", back_populates="project_roles")
    tech_stacks = relationship("TechStack", secondary=ProjectRoleTechStack.__tablename__, back_populates="project_roles")
    team_members = relationship("TeamMember", secondary=TeamMemberProjectRole.__tablename__, back_populates="project_roles")
    applications = relationship("ProjectRoleApplication", back_populates="project_role")


class ProjectRoleApplication(Base):
    __tablename__ = "PROJECT_ROLE_APPLICATION"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    project_title = Column(String(100))
    project_role_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), nullable=False)
    project_role_title = Column(String(100))
    project_description = Column(Text)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    status = Column(String(20))
    motivation_letter = Column(Text)
    rejection_reason = Column(Text)
    applied_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    project_role = relationship("ProjectRole", back_populates="applications")
    user = relationship("User", back_populates="project_role_applications")
    project = relationship("Project", back_populates="project_role_applications")
    selected_key_features = relationship("KeyFeature", secondary=ProjectRoleApplicationKeyFeature.__tablename__, back_populates="applications")
    selected_project_goals = relationship("ProjectGoal", secondary=ProjectRoleApplicationProjectGoal.__tablename__, back_populates="applications")


class UserSocialLink(Base):
    __tablename__ = "USER_SOCIAL_LINK"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    type = Column(String(50))
    url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="social_links")

    __table_args__ = (
        UniqueConstraint("user_id", "type", name="_user_social_link_uc"),
    )


class Category(Base):
    __tablename__ = "CATEGORY"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    projects = relationship("Project", secondary=ProjectCategory.__tablename__, back_populates="categories")
    users = relationship("User", secondary=UserCategory.__tablename__, back_populates="categories")


class KeyFeature(Base):
    __tablename__ = "KEY_FEATURE"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    feature = Column(String(200), nullable=False)

    project = relationship("Project", back_populates="key_features")
    applications = relationship("ProjectRoleApplication", secondary=ProjectRoleApplicationKeyFeature.__tablename__, back_populates="selected_key_features")


class ProjectGoal(Base):
    __tablename__ = "PROJECT_GOAL"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    goal = Column(String(200), nullable=False)

    project = relationship("Project", back_populates="project_goals")
    applications = relationship("ProjectRoleApplication", secondary=ProjectRoleApplicationProjectGoal.__tablename__, back_populates="selected_project_goals")


class EmbedProjects(Base):
    __tablename__ = "embed_PROJECTS"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    embedding_text = Column(Text, nullable=False)
    embedding_vector = Column(Vector(384))
    last_ingested_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    project = relationship("Project")


class HybridProjectEmbeddings(Base):
    __tablename__ = "hybrid_PROJECT_embeddings"

    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    semantic_embedding = Column(Vector(384))
    structured_features = Column(JSONB)
    hybrid_vector = Column(Vector(422))
    similarity_weights = Column(JSONB)
    last_ingested_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    project = relationship("Project")


class EmbedUsers(Base):
    __tablename__ = "embed_USERS"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    username = Column(String(255), nullable=False)
    embedding_text = Column(Text, nullable=False)
    embedding_vector = Column(Vector(384))
    bio = Column(Text)
    categories = Column(ARRAY(String))
    last_ingested_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User")


class UserProjectSimilarity(Base):
    __tablename__ = "USER_PROJECT_SIMILARITY"

    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), primary_key=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), primary_key=True)
    similarity_score = Column(Float, nullable=False)
    semantic_similarity = Column(Float)
    category_similarity = Column(Float)
    tech_similarity = Column(Float)
    popularity_score = Column(Float)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User")
    project = relationship("Project")

    __table_args__ = (
        Index("idx_user_project_similarity_score", "user_id", "similarity_score"),
        Index("idx_user_project_similarity_user", "user_id"),
        Index("idx_user_project_similarity_project", "project_id"),
    )
 