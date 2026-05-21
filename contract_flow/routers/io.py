print("[IO_MODULE] Loading routers/io.py V2")

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_role
import models
import schemas
import crud
import pandas as pd
from io import BytesIO
from datetime import datetime
from urllib.parse import quote

router = APIRouter(prefix="/io", tags=["io"])

# 导出列顺序（按用户要求编排）
EXPORT_COLUMNS = [
    "platform_account",       # 结账号
    "client_unit",            # 委托单位
    "payer_unit",             # 付款单位
    "project_name",           # 工程名称
    "project_manager_name",   # 项目负责人
    "construction_cycle_months",  # 工程建设周期
    "project_category",       # 工程类别
    "inspection_type",        # 检测类型
    "has_cooperation_unit",   # 合作单位
    "discount_rate",          # 折扣率
    "coordination_fee",       # 配合费
    "labor_fee",              # 劳务费
    "estimated_revenue",      # 预计收入
    # 总价预估组成
    "foundation_inspection",      # 地基基础 JC0001
    "material_inspection",        # 材料检测 JC0002
    "housing_assessment",         # 房屋评估 JC0030
    "foundation_pit_monitoring",  # 基坑监测 JC0005
    "environment_inspection",     # 环境检测 JC0009
    "structure_inspection",       # 结构检测 JC0012
    "bridge_inspection",          # 桥梁检测 JC0013
    "energy_efficiency",          # 能效测评 JC0010
    "civil_defense_inspection",   # 人防检测 JC0014
    "supervision_inspection",     # 监督抽检检测 JC0027
    "lightning_protection",       # 防雷检测 JC0012
    "interior_quality",           # 套内质量检测 JC0028
]

COLUMN_MAP = {
    "platform_account": "结账号",
    "client_unit": "委托单位",
    "payer_unit": "付款单位",
    "project_name": "工程名称",
    "project_manager_name": "项目负责人",
    "construction_cycle_months": "工程建设周期(月)",
    "project_category": "工程类别",
    "inspection_type": "检测类型",
    "has_cooperation_unit": "合作单位",
    "discount_rate": "折扣率(%)",
    "coordination_fee": "配合费(元)",
    "labor_fee": "劳务费(元)",
    "estimated_revenue": "预计收入(元)",
    "foundation_inspection": "地基基础JC0001",
    "material_inspection": "材料检测JC0002",
    "housing_assessment": "房屋评估JC0030",
    "foundation_pit_monitoring": "基坑监测JC0005",
    "environment_inspection": "环境检测JC0009",
    "structure_inspection": "结构检测JC0012",
    "bridge_inspection": "桥梁检测JC0013",
    "energy_efficiency": "能效测评JC0010",
    "civil_defense_inspection": "人防检测JC0014",
    "supervision_inspection": "监督抽检检测JC0027",
    "lightning_protection": "防雷检测JC0012",
    "interior_quality": "套内质量检测JC0028",
}


@router.get("/export")
def export_forms(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    print("[DEBUG] export_forms V2 called")
    forms = crud.list_forms(db, limit=10000)
    data = []
    for f in forms:
        row = {}
        for col in EXPORT_COLUMNS:
            val = getattr(f, col)
            # 布尔值转中文
            if col == "has_cooperation_unit":
                val = "有" if val else "无"
            row[col] = val
        data.append(row)
    df = pd.DataFrame(data)
    # 强制按指定列顺序排列，然后重命名为中文
    df = df[EXPORT_COLUMNS].rename(columns=COLUMN_MAP)
    output = BytesIO()
    now_str = datetime.now().strftime("%m%d_%H%M%S")
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=f"Sheet_{now_str}")
    output.seek(0)
    fname = f"合同流转单_{now_str}.xlsx"
    encoded = quote(fname, safe="")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=contract_forms.xlsx; filename*=UTF-8''{encoded}",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


# 导入保持兼容，支持旧列名也支持新列名
IMPORT_COLUMN_MAP = {
    "结账号": "platform_account",
    "委托单位": "client_unit",
    "付款单位": "payer_unit",
    "工程名称": "project_name",
    "项目负责人": "project_manager_name",
    "工程建设周期(月)": "construction_cycle_months",
    "工程类别": "project_category",
    "检测类型": "inspection_type",
    "合作单位": "has_cooperation_unit",
    "折扣率(%)": "discount_rate",
    "配合费(元)": "coordination_fee",
    "劳务费(元)": "labor_fee",
    "预计收入(元)": "estimated_revenue",
    "地基基础JC0001": "foundation_inspection",
    "材料检测JC0002": "material_inspection",
    "房屋评估JC0030": "housing_assessment",
    "基坑监测JC0005": "foundation_pit_monitoring",
    "环境检测JC0009": "environment_inspection",
    "结构检测JC0012": "structure_inspection",
    "桥梁检测JC0013": "bridge_inspection",
    "能效测评JC0010": "energy_efficiency",
    "人防检测JC0014": "civil_defense_inspection",
    "监督抽检检测JC0027": "supervision_inspection",
    "防雷检测JC0012": "lightning_protection",
    "套内质量检测JC0028": "interior_quality",
}


@router.post("/import")
def import_forms(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 Excel 文件")
    contents = file.file.read()
    df = pd.read_excel(BytesIO(contents))
    success = 0
    failed = 0
    for _, row in df.iterrows():
        try:
            form_data = {}
            for src_col, dst_col in IMPORT_COLUMN_MAP.items():
                val = row.get(src_col)
                if pd.isna(val):
                    if dst_col in ["discount_rate", "coordination_fee", "labor_fee",
                                   "estimated_revenue",
                                   "foundation_inspection", "material_inspection",
                                   "housing_assessment", "foundation_pit_monitoring",
                                   "environment_inspection", "structure_inspection",
                                   "bridge_inspection", "energy_efficiency",
                                   "civil_defense_inspection", "supervision_inspection",
                                   "lightning_protection", "interior_quality"]:
                        val = 0
                    elif dst_col == "has_cooperation_unit":
                        val = False
                    elif dst_col == "construction_cycle_months":
                        val = None
                    else:
                        val = None
                if dst_col == "has_cooperation_unit":
                    val = str(val).strip() == "有" if val else False
                form_data[dst_col] = val
            # 补齐缺失的默认值
            defaults = {
                "business_opportunity_no": "", "project_level": "",
                "project_region": "", "estimated_start_date": "", "actual_start_date": "",
                "contract_total_price": 0, "material_fee": 0, "responsible_person_estimate": 0,
                "estimated_revenue": 0,
                "has_approval_document": False, "has_contract_info_confirmation": False,
                "has_authorization_letter": False, "has_witness_certificate": False,
                "has_sampler_certificate": False, "seal_inspection_contract": False,
                "seal_contract_confirmation": False, "seal_integrity_agreement": False,
                "seal_commitment_letter": False, "seal_other": False, "seal_other_text": "",
                "remark": "", "attachments": [],
            }
            for k, v in defaults.items():
                if k not in form_data:
                    form_data[k] = v
            crud.create_form(db, schemas.ContractFormCreate(**form_data), current_user.id)
            success += 1
        except Exception:
            failed += 1
    return {"success": success, "failed": failed}
