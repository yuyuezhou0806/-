import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class ContractInfo:
    project_name: str = ""
    party_a: str = ""      # 甲方/委托方
    party_b: str = ""      # 乙方/受托方
    amount: float = 0.0    # 合同金额
    amount_words: str = "" # 大写金额
    tax_rate: float = 0.0  # 税率
    tax_amount: float = 0.0 # 税额
    amount_without_tax: float = 0.0 # 不含税价
    sign_date: str = ""    # 签订日期
    sign_location: str = "" # 签订地点
    contract_no: str = ""   # 合同编号
    service_content: List[str] = None # 服务内容
    address_a: str = ""    # 甲方地址
    address_b: str = ""    # 乙方地址
    contact_phone_a: str = "" # 甲方电话
    contact_phone_b: str = "" # 乙方电话
    bank_b: str = ""       # 乙方开户行
    account_b: str = ""    # 乙方账号
    raw_text: str = ""     # 原始文本
    confidence: int = 0    # 解析置信度（成功字段数）

    def __post_init__(self):
        if self.service_content is None:
            self.service_content = []


class ContractParser:
    """检测合同解析器 - 支持多种模板"""

    # 检测相关的公司名关键词（用于识别乙方）
    DETECTION_KEYWORDS = ['检测', '监测', '检验', '测试', '鉴定']
    CONSULTING_KEYWORDS = ['咨询', '顾问']

    def parse(self, text: str) -> ContractInfo:
        info = ContractInfo(raw_text=text)

        # 1. 合同编号
        info.contract_no = self._extract_contract_no(text)

        # 2. 项目名称
        info.project_name = self._extract_project_name(text)

        # 3. 甲乙双方
        info.party_a = self._extract_party_a(text)
        info.party_b = self._extract_party_b(text)

        # 4. 金额信息
        info.amount = self._extract_amount(text)
        info.amount_words = self._extract_amount_words(text)
        info.tax_rate = self._extract_tax_rate(text)
        info.tax_amount = self._extract_tax_amount(text)
        info.amount_without_tax = self._extract_amount_without_tax(text)

        # 5. 签订信息
        info.sign_date = self._extract_sign_date(text)
        info.sign_location = self._extract_sign_location(text)

        # 6. 服务内容
        info.service_content = self._extract_service_content(text)

        # 7. 地址电话银行
        info.address_a = self._extract_address_a(text)
        info.address_b = self._extract_address_b(text)
        info.contact_phone_a = self._extract_phone_a(text)
        info.contact_phone_b = self._extract_phone_b(text)
        info.bank_b = self._extract_bank_b(text)
        info.account_b = self._extract_account_b(text)

        # 计算置信度
        info.confidence = self._calc_confidence(info)

        return info

    def _calc_confidence(self, info: ContractInfo) -> int:
        """计算解析置信度：成功提取的字段数"""
        score = 0
        if info.project_name: score += 2
        if info.party_a: score += 2
        if info.party_b: score += 2
        if info.amount > 0: score += 2
        if info.sign_date: score += 1
        if info.contract_no: score += 1
        if info.contact_phone_a or info.contact_phone_b: score += 1
        if info.bank_b: score += 1
        return score

    def _is_detection_company(self, name: str) -> bool:
        """判断是否检测公司（乙方特征）"""
        name = name.lower()
        has_detection = any(kw in name for kw in self.DETECTION_KEYWORDS)
        return has_detection

    def _clean_company_name(self, name: str) -> str:
        """清理公司名称，去掉前缀后缀"""
        name = name.strip()
        # 去掉常见的类型前缀
        prefixes = ['甲方（委托单位）', '甲方(委托单位)', '甲方', '委托方',
                    '乙方（检测机构）', '乙方(检测机构)', '乙方', '受托方',
                    '建设/实施单位', '总承包单位',
                    '单位名称', '（甲方）', '（乙方）',
                    '：', ':', '，', ',']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        # 去掉末尾的章/签字等
        name = re.sub(r'(合同专用章|单位公章|法定代表|委托代理人|经办人).*$', '', name).strip()
        return name

    def _extract_contract_no(self, text: str) -> str:
        """提取合同编号"""
        patterns = [
            r'合同编号[：:]\s*([A-Za-z0-9\-_]+)',
            r'编号[：:]\s*([A-Za-z0-9\-_]+)',
            r'(\d{4}-\d{4}合同\d{4}-[A-Z]+-\d+)',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_project_name(self, text: str) -> str:
        """提取项目名称/工程名称"""
        patterns = [
            # 标准模板：工程名称：xxx
            r'工程名称[：:]\s*\n?\s*([^\n]+?(?:\n[^\n]+?){0,2})\s*(?:工程地址|检测类别|根据《)',
            r'工程名称[：:]\s*\n?\s*([^\n]+)',
            # 技术服务合同：项目名称：
            r'项目名称[：:]\s*\n?\s*([^\n]+)',
            # 从合同标题推断
            r'就([^\n]+?)检测的技术服务',
            # 从描述推断
            r'被检测房屋位于[^，]*，?检测范围',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                name = m.group(1).strip()
                # 清理：去掉工程地址及之后的内容
                name = re.sub(r'工程地址.*$', '', name)
                # 清理其他后缀
                name = re.sub(r'检测.*$', '', name)
                name = re.sub(r'（水利部分）', '', name)
                name = re.sub(r'\n', '', name)
                if len(name) > 3:
                    return name
        return ""

    def _extract_party_a(self, text: str) -> str:
        """提取甲方/委托方"""
        patterns = [
            # 标准模板格式
            r'甲方[（(]委托单位[)）][，:,：]\s*\n?\s*([^\n]+)',
            r'甲方[（(]委托单位[)）]\s*\n?\s*([^\n]+)',
            r'建设/实施单位[：:]\s*\n?\s*([^\n]+)',
            # 传统格式
            r'委托方[：:]\s*\n?\s*(?:\([^)]*\))?\s*\n?\s*([^\n]+)',
            r'甲方[：:]\s*\n?\s*([^\n]+)',
            r'单位名称\s*\n?\s*([^\n]+)(?=\s*合同专用章|\s*或\s*单位公章)',
        ]
        candidates = []
        for p in patterns:
            matches = re.findall(p, text)
            for m in matches:
                name = self._clean_company_name(m)
                if len(name) > 5 and '公司' in name and not self._is_detection_company(name):
                    candidates.append(name)

        # 去重并返回最长的（通常最完整）
        seen = set()
        for name in candidates:
            if name not in seen:
                seen.add(name)
                return name
        return ""

    def _extract_party_b(self, text: str) -> str:
        """提取乙方/受托方"""
        patterns = [
            # 标准模板格式
            r'乙方[（(]检测机构[)）][，:,：]\s*\n?\s*([^\n]+)',
            r'乙方[（(]检测机构[)）]\s*\n?\s*([^\n]+)',
            # 传统格式
            r'受托方[：:]\s*\n?\s*(?:\([^)]*\))?\s*\n?\s*([^\n]+)',
            r'乙方[：:]\s*\n?\s*([^\n]+)',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                name = self._clean_company_name(m.group(1))
                if len(name) > 5:
                    return name

        # fallback：找包含检测关键词的公司名
        matches = re.findall(r'([^\n]{5,50}检测[^\n]{0,30}公司)', text)
        for m in matches:
            name = self._clean_company_name(m)
            if len(name) > 10 and self._is_detection_company(name):
                return name
        return ""

    def _extract_amount(self, text: str) -> float:
        """提取合同金额 - 优先匹配固定金额，避免被费用明细表干扰"""
        # 1. 先找固定金额（最可靠）
        patterns = [
            r'(?:优惠后总费用|本项目报酬暂定|暂定|报酬)\s*[:：]?\s*(?:人民币)?\s*(\d[\d,]+(?:\.\d+)?)\s*元',
            r'检测费用\s*[:：]?\s*(?:人民币)?\s*(\d[\d,]+(?:\.\d+)?)\s*元',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                val = float(m.group(1).replace(',', ''))
                if val > 1000:  # 过滤掉明显是单价的小数字
                    return val

        # 2. 找费用清单总计
        m = re.search(r'8\s*折\s*优\s*惠\s*后\s*\n?\s*(\d[\d,]+)', text)
        if m:
            val = float(m.group(1).replace(',', ''))
            if val > 1000:
                return val

        # 3. 合计
        m = re.search(r'合计\s*\n?\s*(\d[\d,]+)\s*元', text)
        if m:
            val = float(m.group(1).replace(',', ''))
            if val > 1000:
                return val

        return 0.0

    def _extract_amount_words(self, text: str) -> str:
        """提取大写金额"""
        patterns = [
            r'大写[：:]\s*([^\n]+?)(?:[，。]|整）)',
            r'人民币大写([^\n]+?)(?:[，。]|整）)',
            r'大写[：:]\s*([^\n]{5,30})',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                result = m.group(1).strip()
                if any(c in result for c in '零一二三四五六七八九十百千万亿壹贰叁肆伍陆柒捌玖拾佰仟'):
                    return result
        return ""

    def _extract_tax_rate(self, text: str) -> float:
        """提取税率"""
        m = re.search(r'税率\s*(\d+(?:\.\d+)?)\s*%', text)
        if m:
            return float(m.group(1))
        return 0.0

    def _extract_tax_amount(self, text: str) -> float:
        """提取税额"""
        m = re.search(r'税金(?:为|[:：])\s*(\d[\d,]+(?:\.\d+)?)', text)
        if m:
            return float(m.group(1).replace(',', ''))
        return 0.0

    def _extract_amount_without_tax(self, text: str) -> float:
        """提取不含税价"""
        m = re.search(r'不含税价(?:为)?\s*(\d[\d,]+(?:\.\d+)?)', text)
        if m:
            return float(m.group(1).replace(',', ''))
        return 0.0

    def _extract_sign_date(self, text: str) -> str:
        """提取签订日期"""
        patterns = [
            r'合同订立时间[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'签订日期[：:]\s*(\d{4}年\d{1,2}月\d{1,2}日)',
            r'签订日期[：:]\s*(\d{4}[\.\-/]\d{1,2}[\.\-/]\d{1,2})',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_sign_location(self, text: str) -> str:
        """提取签订地点"""
        patterns = [
            r'合同订立地点[：:]\s*\n?\s*([^\n]+)',
            r'签订地点[：:]\s*\n?\s*([^\n]+)',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                loc = m.group(1).strip()
                # 过滤掉页码
                if re.match(r'^-\d+-?$', loc):
                    continue
                if '页' in loc:
                    continue
                return loc
        return ""

    def _extract_service_content(self, text: str) -> List[str]:
        """提取检测服务内容"""
        content = []
        # 匹配"数字）检测内容；"格式
        matches = re.findall(r'\d+\s*[）.)]\s*([^；;。\n]+(?:检测|评估|调查)[^；;。\n]*)', text)
        for m in matches:
            item = m.strip()
            if len(item) > 3 and len(item) < 50 and item not in content:
                content.append(item)

        # 匹配标准模板中的检测项目（混凝土工程类【水利】等）
        matches = re.findall(r'([一-龥]+工程类【[^】]+】)', text)
        for m in matches:
            if m not in content:
                content.append(m)

        return content[:10]

    def _extract_address_a(self, text: str) -> str:
        """提取甲方地址"""
        sections = re.split(r'(?:乙方|受托方)', text)
        if len(sections) >= 2:
            first_part = sections[0]
            m = re.search(r'地址\s*\n?\s*([^\n]{10,60})', first_part)
            if m:
                addr = m.group(1).strip()
                if '号' in addr or '路' in addr or '区' in addr:
                    return addr
        return ""

    def _extract_address_b(self, text: str) -> str:
        """提取乙方地址"""
        sections = re.split(r'(?:乙方|受托方)', text)
        if len(sections) >= 2:
            b_part = sections[1][:2000]
            m = re.search(r'地址\s*\n?\s*([^\n]{10,60})', b_part)
            if m:
                addr = m.group(1).strip()
                if '号' in addr or '路' in addr or '区' in addr:
                    return addr

        m = re.search(r'(杨浦区[^\n]{10,50})', text)
        if m:
            return m.group(1).strip()
        return ""

    def _extract_phone_a(self, text: str) -> str:
        """提取甲方电话 - 在甲方区块"""
        sections = re.split(r'(?:乙方|受托方)', text)
        if len(sections) >= 2:
            first_part = sections[0]
            m = re.search(r'电话\s*\n?\s*(\d[\d\-]{6,15})', first_part)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_phone_b(self, text: str) -> str:
        """提取乙方电话"""
        sections = re.split(r'(?:乙方|受托方)', text)
        if len(sections) >= 2:
            b_part = sections[1][:2000]
            m = re.search(r'电话\s*\n?\s*(\d[\d\-]{6,15})', b_part)
            if m:
                return m.group(1).strip()
            m = re.search(r'联系人手机[：:]\s*(\d{11})', b_part)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_bank_b(self, text: str) -> str:
        """提取乙方开户行"""
        sections = re.split(r'(?:乙方|受托方)', text)
        if len(sections) >= 2:
            b_part = sections[1][:2000]
            m = re.search(r'开户银行\s*\n?\s*([^\n]{5,40})', b_part)
            if m:
                bank = m.group(1).strip()
                if '银行' in bank:
                    return bank

        m = re.search(r'开户银行\s*\n?\s*([^\n]{5,40})', text)
        if m:
            bank = m.group(1).strip()
            if '银行' in bank:
                return bank
        return ""

    def _extract_account_b(self, text: str) -> str:
        """提取乙方账号"""
        sections = re.split(r'(?:乙方|受托方)', text)
        if len(sections) >= 2:
            b_part = sections[1][:2000]
            m = re.search(r'账[号號]\s*\n?\s*(\d[\d\-]{5,30})', b_part)
            if m:
                return m.group(1).strip()

        m = re.search(r'账[号號]\s*\n?\s*(\d[\d\-]{5,30})', text)
        if m:
            return m.group(1).strip()
        return ""


def format_result(info: ContractInfo) -> str:
    """格式化输出"""
    lines = []
    lines.append("=" * 50)
    lines.append(f"合同解析结果 (置信度: {info.confidence}/10)")
    lines.append("=" * 50)
    lines.append(f"合同编号: {info.contract_no}")
    lines.append(f"项目名称: {info.project_name}")
    lines.append(f"甲方: {info.party_a}")
    lines.append(f"乙方: {info.party_b}")
    lines.append(f"签订日期: {info.sign_date}")
    lines.append(f"签订地点: {info.sign_location}")
    lines.append("")
    lines.append(f"合同金额: {info.amount:,.2f} 元")
    lines.append(f"大写金额: {info.amount_words}")
    lines.append(f"税率: {info.tax_rate}%")
    lines.append(f"税额: {info.tax_amount:,.2f} 元")
    lines.append(f"不含税价: {info.amount_without_tax:,.2f} 元")
    lines.append("")
    lines.append(f"甲方地址: {info.address_a}")
    lines.append(f"甲方电话: {info.contact_phone_a}")
    lines.append(f"乙方地址: {info.address_b}")
    lines.append(f"乙方电话: {info.contact_phone_b}")
    lines.append(f"乙方开户行: {info.bank_b}")
    lines.append(f"乙方账号: {info.account_b}")
    lines.append("")
    if info.service_content:
        lines.append("检测内容:")
        for i, item in enumerate(info.service_content, 1):
            lines.append(f"  {i}. {item}")
    lines.append("=" * 50)
    return "\n".join(lines)


def main():
    import sys

    if len(sys.argv) < 2:
        print("usage: python parse_contract.py <txt file>")
        sys.exit(1)

    txt_path = sys.argv[1]
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()

    parser = ContractParser()
    info = parser.parse(text)

    print(format_result(info))

    # save JSON
    output_path = Path(txt_path).with_suffix('.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(info), f, ensure_ascii=False, indent=2)
    print(f"\n[OK] JSON saved: {output_path}")


if __name__ == "__main__":
    main()
