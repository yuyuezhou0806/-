from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    real_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="agent")  # admin, agent
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    projects = relationship("Project", back_populates="agent")
    logs = relationship("ProjectLog", back_populates="user")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_name = Column(String)
    contact_phone = Column(String)
    industry = Column(String)  # 所属细分行业
    employee_count = Column(Integer)
    annual_revenue = Column(Float)
    digital_level = Column(String)  # level_2, level_3, level_4, unknown
    address = Column(String)
    remark = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    projects = relationship("Project", back_populates="client")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_no = Column(String, unique=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    project_name = Column(String, nullable=False)
    digital_level = Column(String, nullable=False)  # level_2, level_3, level_4

    # 合同信息
    contract_type = Column(String)  # two_party, multi_party
    contract_sign_date = Column(String)  # YYYY-MM-DD
    contract_amount = Column(Float, default=0)

    # 进度日期
    implementation_start_date = Column(String)
    implementation_end_date = Column(String)
    audit_report_date = Column(String)
    acceptance_date = Column(String)
    subsidy_approved_date = Column(String)
    subsidy_paid_date = Column(String)

    # 状态
    status = Column(String, default="draft")  # draft, contract_signed, implementing, audit_pending, audit_done, acceptance_pending, accepted, subsidy_approved, subsidy_paid, rejected

    # 补贴计算结果（提交时锁定）
    eligible_total = Column(Float, default=0)
    ineligible_total = Column(Float, default=0)
    estimated_subsidy = Column(Float, default=0)
    approved_subsidy = Column(Float, default=0)
    subsidy_rate_applied = Column(Float, default=0)

    # 合规校验结果快照
    compliance_result = Column(JSON, default=dict)
    rejection_reason = Column(Text)

    # 附件
    attachments = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    client = relationship("Client", back_populates="projects")
    agent = relationship("User", back_populates="projects")
    expenses = relationship("ExpenseItem", back_populates="project", cascade="all, delete-orphan")
    logs = relationship("ProjectLog", back_populates="project", cascade="all, delete-orphan")


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category = Column(String, nullable=False)  # software, cloud_service, hardware_equipment, training, maintenance, consulting, other
    description = Column(String)
    amount = Column(Float, default=0)
    is_subsidiable = Column(Boolean, default=False)
    invoice_no = Column(String)
    invoice_date = Column(String)
    vendor_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="expenses")


class ProjectLog(Base):
    __tablename__ = "project_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # create, update, submit, transition, reject, upload, delete
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="logs")
    user = relationship("User", back_populates="logs")
