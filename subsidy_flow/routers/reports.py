from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud
import policy_engine
from auth import require_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard(
    current_user = Depends(require_user),
    db: Session = Depends(get_db)
):
    stats = crud.get_project_stats(db)
    countdown = policy_engine.get_deadline_countdown()
    return schemas.DashboardStats(
        total_projects=stats["total_projects"],
        draft_count=stats["draft_count"],
        in_progress_count=stats["in_progress_count"],
        accepted_count=stats["accepted_count"],
        subsidy_approved_count=stats["subsidy_approved_count"],
        total_estimated_subsidy=stats["total_estimated_subsidy"],
        total_approved_subsidy=stats["total_approved_subsidy"],
        days_remaining=countdown["days_remaining"],
        deadline=countdown["deadline"],
    )
