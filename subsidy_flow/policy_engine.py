from datetime import date
from typing import List, Dict

POLICY_DEADLINE = date(2026, 12, 31)

DIGITAL_LEVEL_CAPS = {
    "level_2": 600_000,
    "level_3": 2_000_000,
    "level_4": 5_000_000,
}

MAX_SUBSIDY_RATE = 0.50

SUBSIDIABLE_CATEGORIES = {
    "software", "cloud_service", "hardware_equipment",
    "implementation_service", "gateway", "router", "sensor",
    "ai_integrated_machine", "industrial_control_system", "firewall",
}

NON_SUBSIDIABLE_CATEGORIES = {
    "training", "maintenance", "consulting", "other",
}

INDUSTRIES = {
    "intelligent_vehicle": "智能网联与新能源汽车（零部件）",
    "industrial_machine": "工业母机和机器人",
    "fashion_beauty": "时尚美妆",
    "custom_home": "定制家居",
    "clothing": "服装",
    "luggage": "箱包",
    "biomedical": "生物医药（含医疗器械）",
    "food_beverage": "食品饮料",
}

ORIGINAL_6_INDUSTRIES = {
    "intelligent_vehicle", "industrial_machine", "fashion_beauty",
    "custom_home", "clothing", "luggage",
}

NEW_2_INDUSTRIES = {
    "biomedical", "food_beverage",
}


def get_industry_date_rule(industry: str, contract_type: str) -> Dict:
    """获取行业合同日期规则"""
    rule = {"start_date": None, "notes": []}

    if contract_type == "two_party":
        rule["start_date"] = date(2023, 10, 11)
        rule["notes"].append("两方合同签订日期不得早于2023年10月11日")
    elif contract_type == "multi_party":
        if industry in ORIGINAL_6_INDUSTRIES:
            rule["start_date"] = date(2023, 10, 11)
            rule["notes"].append("原6大试点行业多方合同签订日期不得早于牵引单位公示时间（系统按2023年10月11日校验，请人工确认公示时间）")
        elif industry in NEW_2_INDUSTRIES:
            rule["start_date"] = date(2025, 11, 1)
            rule["notes"].append("新增2大试点行业多方合同签订日期不得早于2025年11月1日")
        else:
            rule["start_date"] = date(2023, 10, 11)
            rule["notes"].append("未明确行业，默认按2023年10月11日校验")
    else:
        rule["start_date"] = date(2023, 10, 11)

    return rule


def check_contract_compliance(industry: str, contract_type: str, sign_date_str: str) -> Dict:
    """合同合规校验"""
    reasons = []
    warnings = []
    compliant = True

    try:
        year, month, day = map(int, sign_date_str.split("-"))
        sign_date = date(year, month, day)
    except Exception:
        return {
            "industry": industry,
            "contract_type": contract_type,
            "sign_date": sign_date_str,
            "compliant": False,
            "reasons": ["日期格式错误，请使用 YYYY-MM-DD 格式"],
            "warnings": [],
        }

    # 检查是否超过政策截止日期
    if sign_date > POLICY_DEADLINE:
        compliant = False
        reasons.append(f"合同签订日期（{sign_date_str}）晚于政策截止日期（2026-12-31）")

    # 行业日期规则
    rule = get_industry_date_rule(industry, contract_type)
    min_date = rule["start_date"]

    if min_date and sign_date < min_date:
        compliant = False
        reasons.append(f"合同签订日期（{sign_date_str}）早于允许的最小日期（{min_date.isoformat()}）")
    else:
        reasons.append(f"合同签订日期符合要求（≥ {min_date.isoformat()}）")

    reasons.extend(rule["notes"])

    # 预警
    if sign_date > date(2026, 10, 1):
        warnings.append("合同签订时间已接近政策截止期限，请尽快推进后续流程")

    return {
        "industry": industry,
        "contract_type": contract_type,
        "sign_date": sign_date_str,
        "compliant": compliant,
        "reasons": reasons,
        "warnings": warnings,
    }


def classify_expense(category: str) -> bool:
    """判断费用类别是否可补贴"""
    if category in SUBSIDIABLE_CATEGORIES:
        return True
    if category in NON_SUBSIDIABLE_CATEGORIES:
        return False
    # 默认不可补贴（保守策略）
    return False


def calculate_subsidy(digital_level: str, expense_items: List[Dict]) -> Dict:
    """计算补贴金额"""
    subsidy_cap = DIGITAL_LEVEL_CAPS.get(digital_level, 0)

    eligible_total = 0.0
    ineligible_total = 0.0
    breakdown = []

    for item in expense_items:
        cat = item.get("category", "other")
        amount = float(item.get("amount", 0))
        is_sub = classify_expense(cat)

        breakdown.append({
            "category": cat,
            "amount": amount,
            "subsidiable": is_sub,
            "included": is_sub,
        })

        if is_sub:
            eligible_total += amount
        else:
            ineligible_total += amount

    raw_subsidy = eligible_total * MAX_SUBSIDY_RATE
    final_subsidy = min(raw_subsidy, subsidy_cap)
    applied_rate = MAX_SUBSIDY_RATE if raw_subsidy <= subsidy_cap else (subsidy_cap / eligible_total if eligible_total > 0 else 0)

    note = f"可补贴投入合计 {eligible_total:,.2f} 元，按 {MAX_SUBSIDY_RATE*100:.0f}% 计算为 {raw_subsidy:,.2f} 元"
    if raw_subsidy > subsidy_cap:
        note += f"，已超过 {digital_level.replace('_', '')} 级上限 {subsidy_cap:,.2f} 元，最终按上限核定"
    else:
        note += f"，未超过 {digital_level.replace('_', '')} 级上限 {subsidy_cap:,.2f} 元"

    return {
        "digital_level": digital_level,
        "eligible_total": eligible_total,
        "ineligible_total": ineligible_total,
        "subsidy_cap": subsidy_cap,
        "max_subsidy_rate": MAX_SUBSIDY_RATE,
        "estimated_subsidy": final_subsidy,
        "applied_rate": applied_rate,
        "breakdown": breakdown,
        "note": note,
    }


def quick_calculate(digital_level: str, total_investment: float) -> Dict:
    """快速估算（无明细时，假设全部可补贴）"""
    subsidy_cap = DIGITAL_LEVEL_CAPS.get(digital_level, 0)
    raw_subsidy = total_investment * MAX_SUBSIDY_RATE
    final_subsidy = min(raw_subsidy, subsidy_cap)

    level_name = {"level_2": "二级", "level_3": "三级", "level_4": "四级"}.get(digital_level, digital_level)
    note = f"{level_name}企业补贴上限为 {subsidy_cap:,.0f} 元。按投入 {total_investment:,.2f} 元的 {MAX_SUBSIDY_RATE*100:.0f}% 计算，预估可获得补贴 {final_subsidy:,.2f} 元。"
    if raw_subsidy > subsidy_cap:
        note += f"（已达上限）"

    return {
        "digital_level": digital_level,
        "total_investment": total_investment,
        "max_subsidy_rate": MAX_SUBSIDY_RATE,
        "subsidy_cap": subsidy_cap,
        "estimated_subsidy": final_subsidy,
        "note": note,
    }


def get_deadline_countdown() -> Dict:
    """获取截止日期倒计时"""
    today = date.today()
    delta = (POLICY_DEADLINE - today).days
    return {
        "deadline": POLICY_DEADLINE.isoformat(),
        "days_remaining": delta,
        "is_expired": delta < 0,
    }


def get_policy_summary() -> List[Dict]:
    """政策要点结构化摘要"""
    return [
        {
            "title": "政策有效期",
            "content": "省级城市试点政策延期至 2026 年 12 月 31 日。",
            "highlight": "2026-12-31",
            "tag": "时效",
        },
        {
            "title": "奖补范围",
            "content": "支持购买数字化改造相关的软件、云服务及必要的实施服务，网关、路由、传感器、大模型一体机、工业控制系统、防火墙等必要的数据采集传输、工业控制、信息安全设备。",
            "highlight": "软件、云服务、设备",
            "tag": "范围",
        },
        {
            "title": "不含税支出",
            "content": "不包括培训费、维保费等相关支出，且不含税。",
            "highlight": "不含培训费、维保费",
            "tag": "排除",
        },
        {
            "title": "三级资金累计补助比例",
            "content": "中央、省、市三级资金累计按照不超过企业数字化改造项目核定投入的 50% 给予补助。",
            "highlight": "不超过 50%",
            "tag": "比例",
        },
        {
            "title": "二级企业补贴上限",
            "content": "数字化水平等级达到二级的企业累计补助不超过 60 万元。",
            "highlight": "60 万元",
            "tag": "额度",
        },
        {
            "title": "三级企业补贴上限",
            "content": "三级的企业累计补助从不超过 100 万元提高到不超过 200 万元。",
            "highlight": "200 万元",
            "tag": "额度",
        },
        {
            "title": "四级企业补贴上限",
            "content": "四级的企业累计补助从不超过 150 万元提高到不超过 500 万元。",
            "highlight": "500 万元",
            "tag": "额度",
        },
        {
            "title": "8 大试点行业",
            "content": "智能网联与新能源汽车（零部件）、工业母机和机器人、时尚美妆、定制家居、服装、箱包、生物医药（含医疗器械）、食品饮料。",
            "highlight": "8 大行业",
            "tag": "行业",
        },
        {
            "title": "新增行业合同时间要求",
            "content": "生物医药、食品饮料新增试点行业，多方合同签订日期不得早于 2025 年 11 月 1 日。",
            "highlight": "2025-11-01",
            "tag": "合规",
        },
        {
            "title": "专项审计与验收",
            "content": "项目入库申报前需配合第三方会计师事务所开展投资额专项审计；所有申报奖补项目均须验收，现场验收比例不低于 30%。",
            "highlight": "现场验收 ≥ 30%",
            "tag": "审计",
        },
    ]
