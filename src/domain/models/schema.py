import datetime
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
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
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    team_memberships = relationship("TeamMember", back_populates="user")
    contributions = relationship("Contribution", back_populates="user")
    applications = relationship("Application", back_populates="user")


class Project(Base):
    __tablename__ = "PROJECT"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    roles = relationship("ProjectRole", back_populates="project")
    team_members = relationship("TeamMember", back_populates="project")
    contributions = relationship("Contribution", back_populates="project")


class ProjectRole(Base):
    __tablename__ = "PROJECT_ROLE"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="roles")
    applications = relationship("Application", back_populates="role")


# --- "Strong Interest" Linking Tables ---


class TeamMember(Base):
    __tablename__ = "TEAM_MEMBER"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="team_memberships")
    project = relationship("Project", back_populates="team_members")

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="_user_project_uc"),
    )


class Contribution(Base):
    __tablename__ = "CONTRIBUTION"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("PROJECT.id"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    title = Column(String(200))
    type = Column(String(50))

    user = relationship("User", back_populates="contributions")
    project = relationship("Project", back_populates="contributions")


class Application(Base):
    __tablename__ = "APPLICATION"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("USER.id"), nullable=False)
    project_role_id = Column(
        UUID(as_uuid=True), ForeignKey("PROJECT_ROLE.id"), nullable=False
    )
    applied_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    status = Column(String(50), default="pending")

    user = relationship("User", back_populates="applications")
    role = relationship("ProjectRole", back_populates="applications")

    __table_args__ = (
        UniqueConstraint("user_id", "project_role_id", name="_user_role_uc"),
    )
