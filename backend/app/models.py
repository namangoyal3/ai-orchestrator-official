from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


def generate_api_key():
    import secrets
    return f"gw-{secrets.token_urlsafe(32)}"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="starter")  # starter, pro, enterprise
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    requests = relationship("RequestLog", back_populates="organization")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=False)  # first 8 chars for display
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON, default=list)  # ["read", "write", "admin"]
    rate_limit_rpm = Column(Integer, default=60)
    rate_limit_daily = Column(Integer, default=10000)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    organization = relationship("Organization", back_populates="api_keys")


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=True)

    # Request details
    prompt = Column(Text, nullable=False)
    context_url = Column(String(2048), nullable=True)
    context_type = Column(String(50), nullable=True)  # url, document, none

    # Orchestration decisions
    selected_llm = Column(String(100), nullable=True)
    selected_agents = Column(JSON, default=list)
    selected_tools = Column(JSON, default=list)
    task_category = Column(String(100), nullable=True)
    complexity_score = Column(Float, nullable=True)

    # Response
    response = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    # Metrics
    latency_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="requests")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    capabilities = Column(JSON, default=list)
    required_tools = Column(JSON, default=list)
    preferred_llm = Column(String(100), default="auto")
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    icon = Column(String(50), default="🤖")
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())


class Tool(Base):
    __tablename__ = "tools"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    provider = Column(String(100), nullable=True)
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    requires_auth = Column(Boolean, default=False)
    auth_fields = Column(JSON, default=list)
    parameters_schema = Column(JSON, default=dict)
    icon = Column(String(50), default="🔧")
    created_at = Column(DateTime, server_default=func.now())


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    llm_usage = Column(JSON, default=dict)  # {"claude-opus-4-6": 50, ...}
    agent_usage = Column(JSON, default=dict)
    tool_usage = Column(JSON, default=dict)


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), index=True, nullable=True)
    description = Column(Text, nullable=True)
    demand_score = Column(Float, default=0.0)
    source = Column(String(100), default="skillsmp")  # e.g., skillsmp
    external_url = Column(String(2048), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class MCP(Base):
    __tablename__ = "mcps"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    repo_url = Column(String(2048), nullable=True)
    source = Column(String(100), default="mcpmarket")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(String, primary_key=True)  # Using external ID e.g., 'anthropic/claude-3-opus'
    display_name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    context_length = Column(Integer, default=0)
    cost_per_1m_input = Column(Float, default=0.0)
    cost_per_1m_output = Column(Float, default=0.0)
    source = Column(String(100), default="openrouter")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# Optimize searches across huge datasets
Index('idx_skills_name_cat', Skill.name, Skill.category)
Index('idx_agent_slug', Agent.slug)
Index('idx_tool_slug', Tool.slug)
