from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ===================== 用户 =====================
class UserBase(BaseModel):
    username: str
    real_name: str
    role: str = "agent"


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ===================== 客户 =====================
class ClientBase(BaseModel):
    company_name: str
    contact_name: Optional[str] = ""
    contact_phone: Optional[str] = ""
    industry: Optional[str] = ""
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = 0
    digital_level: Optional[str] = "unknown"  # level_2, level_3, level_4, unknown
    address: Optional[str] = ""
    remark: Optional[str] = ""


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== 投资明细 =====================
class ExpenseItemBase(BaseModel):
    category: str
    description: Optional[str] = ""
    amount: float = 0
    is_subsidiable: Optional[bool] = None
    invoice_no: Optional[str] = ""
    invoice_date: Optional[str] = ""
    vendor_name: Optional[str] = ""


class ExpenseItemCreate(ExpenseItemBase):
    pass


class ExpenseItemOut(ExpenseItemBase):
    id: int
    project_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== 项目日志 =====================
class ProjectLogOut(BaseModel):
    id: int
    project_id: int
    user_id: int
    action: str
    comment: Optional[str] = ""
    created_at: Optional[datetime] = None
    user_name: Optional[str] = ""

    class Config:
        from_attributes = True


# ===================== 项目 =====================
class ProjectBase(BaseModel):
    project_name: str
    digital_level: str  # level_2, level_3, level_4
    contract_type: Optional[str] = ""  # two_party, multi_party
    contract_sign_date: Optional[str] = ""
    contract_amount: Optional[float] = 0
    implementation_start_date: Optional[str] = ""
    implementation_end_date: Optional[str] = ""


class ProjectCreate(ProjectBase):
    client_id: int


class ProjectUpdate(ProjectBase):
    pass


class ProjectOut(ProjectBase):
    id: int
    project_no: Optional[str] = ""
    client_id: int
    agent_id: int
    status: str
    eligible_total: float
    ineligible_total: float
    estimated_subsidy: float
    approved_subsidy: float
    subsidy_rate_applied: float
    compliance_result: Optional[dict] = None
    rejection_reason: Optional[str] = ""
    attachments: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    client_name: Optional[str] = ""
    agent_name: Optional[str] = ""
    expenses: List[ExpenseItemOut] = []
    logs: List[ProjectLogOut] = []

    class Config:
        from_attributes = True


class ProjectListItem(BaseModel):
    id: int
    project_no: Optional[str] = ""
    project_name: str
    client_name: Optional[str] = ""
    status: str
    digital_level: Optional[str] = ""
    contract_sign_date: Optional[str] = ""
    estimated_subsidy: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectTransition(BaseModel):
    to_status: str
    comment: Optional[str] = ""


# ===================== 公开工具 =====================
class SubsidyCalcRequest(BaseModel):
    digital_level: str  # level_2, level_3, level_4
    total_investment: float


class SubsidyCalcResponse(BaseModel):
    digital_level: str
    total_investment: float
    max_subsidy_rate: float
    subsidy_cap: float
    estimated_subsidy: float
    note: str


class ComplianceCheckRequest(BaseModel):
    industry: str
    contract_type: str  # two_party, multi_party
    sign_date: str  # YYYY-MM-DD


class ComplianceCheckResponse(BaseModel):
    industry: str
    contract_type: str
    sign_date: str
    compliant: bool
    reasons: List[str]
    warnings: List[str]


# ===================== 仪表盘 =====================
class DashboardStats(BaseModel):
    total_projects: int
    draft_count: int
    in_progress_count: int
    accepted_count: int
    subsidy_approved_count: int
    total_estimated_subsidy: float
    total_approved_subsidy: float
    days_remaining: int
    deadline: str
