from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    real_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # project_taker, project_manager, dept_head, marketing, tech_quality, admin
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    forms = relationship("ContractForm", back_populates="creator")
    signatures = relationship("Signature", back_populates="user")
    logs = relationship("ApprovalLog", back_populates="user")


class ContractForm(Base):
    __tablename__ = "contract_forms"

    id = Column(Integer, primary_key=True, index=True)
    business_opportunity_no = Column(String, index=True)
    client_unit = Column(String)
    payer_unit = Column(String)
    project_name = Column(String)
    platform_account = Column(String)
    project_manager_name = Column(String)  # 项目负责人姓名（文字输入）

    # 工程类别
    project_category = Column(String)  # 房建/市政基础设施/房屋修缮/轨道交通/水利/民防/公路/绿化/水运/其他
    project_level = Column(String)
    has_approval_document = Column(Boolean, default=False)

    # 检测类型
    inspection_type = Column(String)  # 施工检测,监理平行检测,监督抽检,其他
    project_region = Column(String)
    has_cooperation_unit = Column(Boolean, default=False)
    remark = Column(Text)

    construction_cycle_months = Column(Integer)
    estimated_start_date = Column(String)
    actual_start_date = Column(String)

    # 费用
    contract_total_price = Column(Float, default=0)
    discount_rate = Column(Float, default=0)
    coordination_fee = Column(Float, default=0)
    labor_fee = Column(Float, default=0)
    material_fee = Column(Float, default=0)
    responsible_person_estimate = Column(Float, default=0)
    estimated_revenue = Column(Float, default=0)

    # 二证一书
    has_contract_info_confirmation = Column(Boolean, default=False)
    has_authorization_letter = Column(Boolean, default=False)
    has_witness_certificate = Column(Boolean, default=False)
    has_sampler_certificate = Column(Boolean, default=False)

    # 总价预估组成
    foundation_inspection = Column(Float, default=0)          # 地基基础 JC0001
    material_inspection = Column(Float, default=0)            # 材料检测 JC0002
    housing_assessment = Column(Float, default=0)             # 房屋评估 JC0030
    foundation_pit_monitoring = Column(Float, default=0)      # 基坑监测 JC0005
    environment_inspection = Column(Float, default=0)         # 环境检测 JC0009
    structure_inspection = Column(Float, default=0)           # 结构检测 JC0012
    bridge_inspection = Column(Float, default=0)              # 桥梁检测 JC0013
    energy_efficiency = Column(Float, default=0)              # 能效测评 JC0010
    civil_defense_inspection = Column(Float, default=0)       # 人防检测 JC0014
    supervision_inspection = Column(Float, default=0)         # 监督抽检检测 JC0027
    lightning_protection = Column(Float, default=0)           # 防雷检测 JC0012
    interior_quality = Column(Float, default=0)               # 套内质量检测 JC0028

    # 合同盖章内容确认
    seal_inspection_contract = Column(Boolean, default=False)
    seal_contract_confirmation = Column(Boolean, default=False)
    seal_integrity_agreement = Column(Boolean, default=False)
    seal_commitment_letter = Column(Boolean, default=False)
    seal_other = Column(Boolean, default=False)
    seal_other_text = Column(String)

    # 附件列表，存储文件名数组 JSON
    attachments = Column(JSON, default=list)

    # 状态
    status = Column(String, default="draft")  # draft, pending_manager, pending_dept, pending_marketing, pending_tech, approved, rejected
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User", back_populates="forms")
    signatures = relationship("Signature", back_populates="form")
    logs = relationship("ApprovalLog", back_populates="form")


class Signature(Base):
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("contract_forms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # project_manager, dept_head, marketing, tech_quality, project_taker
    signature_data = Column(Text, nullable=False)  # Base64 PNG
    signed_at = Column(DateTime(timezone=True), server_default=func.now())

    form = relationship("ContractForm", back_populates="signatures")
    user = relationship("User", back_populates="signatures")


class ApprovalLog(Base):
    __tablename__ = "approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("contract_forms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # submit, approve, reject
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    form = relationship("ContractForm", back_populates="logs")
    user = relationship("User", back_populates="logs")
