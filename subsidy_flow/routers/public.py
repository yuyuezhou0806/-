from fastapi import APIRouter
import schemas
import policy_engine

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/calculate", response_model=schemas.SubsidyCalcResponse)
def public_calculate(req: schemas.SubsidyCalcRequest):
    result = policy_engine.quick_calculate(req.digital_level, req.total_investment)
    return schemas.SubsidyCalcResponse(**result)


@router.post("/check-compliance", response_model=schemas.ComplianceCheckResponse)
def public_check_compliance(req: schemas.ComplianceCheckRequest):
    result = policy_engine.check_contract_compliance(req.industry, req.contract_type, req.sign_date)
    return schemas.ComplianceCheckResponse(**result)


@router.get("/policy-summary")
def public_policy_summary():
    return policy_engine.get_policy_summary()


@router.get("/deadline-countdown")
def public_deadline_countdown():
    return policy_engine.get_deadline_countdown()


@router.get("/industries")
def public_industries():
    return [
        {"key": k, "name": v}
        for k, v in policy_engine.INDUSTRIES.items()
    ]
