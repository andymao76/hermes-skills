#!/usr/bin/env python3
"""
一人电商运营助手 / SoloEcom Pilot — 核心模块
选品 · 定价 · 内容 · 客服 · 合规 · 数据诊断

用法: python main.py [module] [args...]
模块: market-intel | pricing | content | compliance | service | analytics
"""

import json
import os
import sys
from typing import Optional

# ─────── 违禁词库 ───────

DEFAULT_BANNED_WORDS = {
    "绝对化用语": ["最", "第一", "唯一", "首个", "最佳", "极品", "顶级", "终极", "绝无仅有", "全网第一"],
    "权威性误导": ["国家级", "世界级", "全网首发", "全国首家", "全球首创", "国礼级"],
    "虚假承诺": ["100%有效", "永久", "包治", "绝对", "根治", "永不褪色", "永不掉色"],
    "夸大功效": ["速效", "神效", "奇效", "立竿见影", "一夜变白", "三天见效"],
    "伪科学": ["科学证明", "医学认证", "诺贝尔奖", "基因治疗"],
    "诱导消费": ["马上抢", "仅剩X件", "不买后悔", "只限今日", "错过等一年"],
    "歧视性": ["最贱", "最低端", "最垃圾"],
}


# ─────── 1. 智能选品 ───────

class MarketIntel:
    CATEGORY_KB = {
        "蓝牙耳机": {"market": 4, "competition": 3, "profit": 3, "seasonal": 4, "supply_chain": 3},
        "手机壳": {"market": 4, "competition": 2, "profit": 4, "seasonal": 5, "supply_chain": 5},
        "家居收纳": {"market": 4, "competition": 4, "profit": 4, "seasonal": 3, "supply_chain": 4},
        "食品零食": {"market": 5, "competition": 3, "profit": 3, "seasonal": 3, "supply_chain": 2},
        "美妆工具": {"market": 4, "competition": 3, "profit": 5, "seasonal": 3, "supply_chain": 4},
        "宠物用品": {"market": 4, "competition": 4, "profit": 4, "seasonal": 4, "supply_chain": 3},
        "数码配件": {"market": 4, "competition": 2, "profit": 3, "seasonal": 5, "supply_chain": 4},
        "手工文创": {"market": 3, "competition": 4, "profit": 5, "seasonal": 3, "supply_chain": 2},
    }

    CATEGORY_ALIASES = {
        "tws": "蓝牙耳机", "耳机": "蓝牙耳机",
        "壳": "手机壳", "手机壳": "手机壳",
        "收纳": "家居收纳", "家居": "家居收纳",
        "零食": "食品零食", "食品": "食品零食",
        "美妆": "美妆工具", "化妆品": "美妆工具",
        "宠物": "宠物用品", "猫": "宠物用品", "狗": "宠物用品",
        "充电器": "数码配件", "数据线": "数码配件",
        "文创": "手工文创", "手作": "手工文创",
    }

    @staticmethod
    def resolve_category(name: str) -> Optional[str]:
        name = name.strip().lower()
        for alias, cat in MarketIntel.CATEGORY_ALIASES.items():
            if alias in name:
                return cat
        # Direct match
        for cat in MarketIntel.CATEGORY_KB:
            if cat in name or name in cat:
                return cat
        return None

    @staticmethod
    def analyze_from_kb(category: str) -> dict:
        if category not in MarketIntel.CATEGORY_KB:
            return {"error": f"品类 '{category}' 不在知识库中"}
        scores = MarketIntel.CATEGORY_KB[category]
        total = sum(scores.values())
        return {
            "category": category,
            "scores": scores,
            "total_score": total,
            "stars": "★" * round(total / 5) + "☆" * (5 - round(total / 5)),
            "recommendation": "推荐" if total >= 20 else ("谨慎" if total >= 15 else "回避"),
            "notes": [
                "毛利率 > 40% 有利润空间" if scores["profit"] >= 4 else "利润率偏低，需控制成本",
                "适合一件代发模式" if scores["supply_chain"] >= 4 else "供应链门槛较高",
                "全年需求稳定，库存压力小" if scores["seasonal"] >= 4 else "需注意季节性波动",
            ],
        }

    @staticmethod
    def analyze_from_questionnaire(answers: dict) -> dict:
        scores = {}
        q_map = {
            "market_hot": ("市场热度", {"高": 5, "中": 3, "低": 1}),
            "brand_count": ("头部品牌占比", {"<30%": 5, "30-60%": 3, ">60%": 1}),
            "avg_margin": ("毛利率", {">40%": 5, "20-40%": 3, "<20%": 1}),
            "seasonal_pattern": ("季节性", {"全年稳定": 5, "略有波动": 3, "季节性明显": 1}),
            "min_order": ("起订量", {"<50件": 5, "50-200件": 3, ">200件": 1}),
        }
        for key, (label, mapping) in q_map.items():
            val = answers.get(key, "")
            scores[label] = mapping.get(val, 1)
        total = sum(scores.values())
        return {
            "scores": scores,
            "total_score": total,
            "stars": "★" * round(total / 5) + "☆" * (5 - round(total / 5)),
            "recommendation": "推荐" if total >= 20 else ("谨慎" if total >= 15 else "回避"),
        }


# ─────── 2. 定价引擎 ───────

class PricingEngine:
    PLATFORM_RATES = {
        "淘宝": {"default": 0.008, "class_rates": {"服装鞋包": 0.005, "3C数码": 0.008, "美妆个护": 0.008}},
        "天猫": {"default": 0.04, "class_rates": {"服装鞋包": 0.05, "3C数码": 0.03, "美妆个护": 0.04}},
        "拼多多": {"default": 0.015, "class_rates": {"服装鞋包": 0.012, "3C数码": 0.015, "美妆个护": 0.01}},
        "抖音": {"default": 0.05, "class_rates": {"服装鞋包": 0.05, "3C数码": 0.03, "美妆个护": 0.08}},
        "小红书": {"default": 0.10, "class_rates": {"服装鞋包": 0.10, "美妆个护": 0.15}},
        "京东": {"default": 0.05, "class_rates": {"服装鞋包": 0.08, "3C数码": 0.05, "美妆个护": 0.06}},
    }

    @staticmethod
    def _get_platform_rate(platform: str, category: str) -> float:
        plat = PricingEngine.PLATFORM_RATES.get(platform)
        if not plat:
            return 0.05
        return plat["class_rates"].get(category, plat["default"])

    @staticmethod
    def calculate_price(cost: float, platform: str, category: str = "",
                        target_margin: float = 0.3, shipping: float = 0,
                        packaging: float = 0) -> dict:
        total_cost = (cost + packaging + shipping) * 1.04  # +4% return loss
        rate = PricingEngine._get_platform_rate(platform, category)
        marketing = 0.08

        conservative_price = total_cost / (1 - rate - marketing - 0.20)
        suggested_price = total_cost / (1 - rate - marketing - target_margin)
        aggressive_price = total_cost / (1 - rate - marketing - 0.40)

        return {
            "cost_breakdown": {
                "采购成本": round(cost, 2),
                "包装": round(packaging, 2),
                "物流": round(shipping, 2),
                "退换货损耗": round(total_cost - cost - packaging - shipping, 2),
                "总成本": round(total_cost, 2),
            },
            "prices": {
                "保守价(毛利率20%)": round(conservative_price, 2),
                "建议价(毛利率30%)": round(suggested_price, 2),
                "激进价(毛利率40%)": round(aggressive_price, 2),
            },
            "platform_rate": rate,
            "marketing_reserve": marketing,
        }


# ─────── 3. 广告法合规检查 ───────

class AdComplianceChecker:
    def __init__(self, wordlist_path: Optional[str] = None):
        self.wordlist = dict(DEFAULT_BANNED_WORDS)
        if wordlist_path and os.path.exists(wordlist_path):
            with open(wordlist_path, "r", encoding="utf-8") as f:
                custom = json.load(f)
                for k, v in custom.items():
                    if k in self.wordlist:
                        self.wordlist[k].extend(v)
                    else:
                        self.wordlist[k] = v

    def check_text(self, text: str) -> list:
        findings = []
        for category, words in self.wordlist.items():
            for word in words:
                if word in text.lower() or word in text:
                    findings.append({
                        "category": category,
                        "word": word,
                        "level": "🔴 高" if category in ("绝对化用语", "虚假承诺", "虚假宣传") else "🟡 中",
                        "suggestion": DEFAULT_REPLACEMENTS.get(word, f"替换 '{word}' 为更温和的表达"),
                    })
        return findings

    def generate_compliance_report(self, text: str) -> dict:
        findings = self.check_text(text)
        if not findings:
            return {"pass": True, "message": "✅ 合规检查通过，未发现违规词", "findings": []}
        high = [f for f in findings if "🔴" in f["level"]]
        medium = [f for f in findings if "🟡" in f["level"]]
        return {
            "pass": len(high) == 0,
            "message": f"发现 {len(high)} 项高风险 + {len(medium)} 项中风险违规",
            "findings": findings,
            "risk_summary": {
                "high": len(high),
                "medium": len(medium),
            },
        }


DEFAULT_REPLACEMENTS = {
    "最": "很/非常/相当", "第一": "优选/热门/畅销",
    "唯一": "少有/稀有", "首个": "创新/先行",
    "最佳": "优选/热门之选", "极品": "精品/优质",
    "顶级": "高端/优质", "国家级": "品牌自研/匠心打造",
    "世界级": "行业领先/品质卓越",
    "100%有效": "持久/显著", "永久": "持久/长期",
    "包治": "改善/缓解", "绝对": "显著/明显",
    "速效": "逐步改善/持续使用", "神效": "显著效果",
    "奇效": "不错的效果", "立竿见影": "持续使用效果明显",
    "科学证明": "实验室测试/用户实测",
}


# ─────── CLI 入口 ───────

def main():
    if len(sys.argv) < 2:
        print("用法: python main.py [module]")
        print("模块: market-intel | pricing | content | compliance | service | analytics")
        print("无参数时运行交互式 demo:")
        demo()
        return

    module = sys.argv[1]
    if module == "market-intel":
        cat = sys.argv[2] if len(sys.argv) > 2 else "蓝牙耳机"
        mi = MarketIntel()
        resolved = mi.resolve_category(cat)
        if resolved:
            report = mi.analyze_from_kb(resolved)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"品类 '{cat}' 未在知识库中找到，请使用交互式问卷")
    elif module == "pricing":
        cost = float(sys.argv[2]) if len(sys.argv) > 2 else 50
        platform = sys.argv[3] if len(sys.argv) > 3 else "淘宝"
        pe = PricingEngine()
        result = pe.calculate_price(cost=cost, platform=platform)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif module == "compliance":
        text = sys.argv[2] if len(sys.argv) > 2 else "我们的产品是全国第一，100%有效"
        checker = AdComplianceChecker()
        report = checker.generate_compliance_report(text)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"未知模块: {module}")
        print("可用: market-intel | pricing | content | compliance | service | analytics")


def demo():
    print("=" * 50)
    print("一人电商运营助手 / SoloEcom Pilot — Demo")
    print("=" * 50)

    # 1. 选品
    print("\n📦 智能选品 Demo")
    mi = MarketIntel()
    for cat in ["蓝牙耳机", "手机壳", "手工文创"]:
        report = mi.analyze_from_kb(cat)
        print(f"  {cat}: {report['stars']} {report['recommendation']}")

    # 2. 定价
    print("\n💰 定价引擎 Demo")
    pe = PricingEngine()
    r = pe.calculate_price(cost=50, platform="抖音", category="美妆个护")
    print(f"  总成本: {r['cost_breakdown']['总成本']}元")
    for k, v in r['prices'].items():
        print(f"  {k}: {v}元")
    print(f"  平台扣点: {r['platform_rate']*100:.1f}%")

    # 3. 合规检查
    print("\n⚠️ 合规检查 Demo")
    checker = AdComplianceChecker()
    r = checker.generate_compliance_report("我们的产品是全国第一，100%有效，国家级认证")
    print(f"  结果: {r['message']}")
    for f in r['findings']:
        print(f"  {f['level']} '{f['word']}' → {f['suggestion']}")


if __name__ == "__main__":
    main()
