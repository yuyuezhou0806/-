from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ===================== 用户 =====================
class UserBase(BaseModel):
    username: str
    real_name: str
    role: str


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


# ===================== 签名 =====================
class SignatureBase(BaseModel):
    role: str
    signature_data: str


class SignatureOut(SignatureBase):
    id: int
    form_id: int
    user_id: int
    signed_at: Optional[datetime] = None
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True


# ===================== 审批日志 =====================
class ApprovalLogBase(BaseModel):
    action: str
    comment: Optional[str] = None


class ApprovalLogOut(ApprovalLogBase):
    id: int
    form_id: int
    user_id: int
    created_at: Optional[datetime] = None
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True


# ===================== 合同表单 =====================
class ContractFormBase(BaseModel):
    business_opportunity_no: Optional[str] = ""
    client_unit: Optional[str] = ""
    payer_unit: Optional[str] = ""
    project_name: Optional[str] = ""
    platform_account: Optional[str] = ""
    project_manager_name: Optional[str] = ""

    project_category: Optional[str] = ""
    project_level: Optional[str] = ""
    has_approval_document: bool = False

    inspection_type: Optional[str] = ""
    project_region: Optional[str] = ""
    has_cooperation_unit: bool = False
    remark: Optional[str] = ""

    construction_cycle_months: Optional[int] = None
    estimated_start_date: Optional[str] = ""
    actual_start_date: Optional[str] = ""

    contract_total_price: float = 0
    discount_rate: float = 0
    coordination_fee: float = 0
    labor_fee: float = 0
    material_fee: float = 0
    responsible_person_estimate: float = 0
    estimated_revenue: float = 0

    has_contract_info_confirmation: bool = False
    has_authorization_letter: bool = False
    has_witness_certificate: bool = False
    has_sampler_certificate: bool = False

    foundation_inspection: float = 0
    material_inspection: float = 0
    housing_assessment: float = 0
    foundation_pit_monitoring: float = 0
    environment_inspection: float = 0
    structure_inspection: float = 0
    bridge_inspection: float = 0
    energy_efficiency: float = 0
    civil_defense_inspection: float = 0
    supervision_inspection: float = 0
    lightning_protection: float = 0
    interior_quality: float = 0

    seal_inspection_contract: bool = False
    seal_contract_confirmation: bool = False
    seal_integrity_agreement: bool = False
    seal_commitment_letter: bool = False
    seal_other: bool = False
    seal_other_text: Optional[str] = ""

    attachments: List[str] = []


class ContractFormCreate(ContractFormBase):
    pass


class ContractFormUpdate(ContractFormBase):
    pass


class ContractFormOut(ContractFormBase):
    id: int
    status: str
    created_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator: Optional[UserOut] = None
    signatures: List[SignatureOut] = []
    logs: List[ApprovalLogOut] = []

    class Config:
        from_attributes = True


class SubmitAction(BaseModel):
    action: str  # submit / approve / reject
    comment: Optional[str] = ""
    signature_data: Optional[str] = ""


class FormListItem(BaseModel):
    id: int
    business_opportunity_no: Optional[str] = ""
    project_name: Optional[str] = ""
    client_unit: Optional[str] = ""
    platform_account: Optional[str] = ""
    status: str
    created_at: Optional[datetime] = None
    creator_name: Optional[str] = ""
    attachments: List[str] = []

    class Config:
        from_attributes = True
