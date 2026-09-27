"""
Regional Training Capacity Dataset and Demand Gap Analysis for Nivara.
Contains illustrative training center capacity figures for the 5 supported regions:
Delhi, Maharashtra, Tamil Nadu, Karnataka, and Uttar Pradesh.
"""
from typing import Dict, Any, List, Optional
import nsqf_rules

CAPACITY_DISCLAIMER = "Estimated capacity — illustrative, pending integration with Skill India Digital Hub"

ESTIMATED_CAPACITY_DATA: Dict[str, Dict[str, int]] = {
    "Delhi": {
        "apparel_tailoring": 15,
        "digital_csc": 25,
        "solar_technician": 30,
        "automotive_ev": 20,
        "food_processing": 12,
        "healthcare_assistant": 35
    },
    "Maharashtra": {
        "solar_technician": 40,
        "food_processing": 45,
        "automotive_ev": 35,
        "apparel_tailoring": 30,
        "digital_csc": 50,
        "healthcare_assistant": 40
    },
    "Tamil Nadu": {
        "automotive_ev": 50,
        "solar_technician": 35,
        "apparel_tailoring": 40,
        "food_processing": 25,
        "digital_csc": 45,
        "healthcare_assistant": 30
    },
    "Karnataka": {
        "digital_csc": 60,
        "apparel_tailoring": 30,
        "solar_technician": 35,
        "automotive_ev": 30,
        "food_processing": 20,
        "healthcare_assistant": 35
    },
    "Uttar Pradesh": {
        "food_processing": 50,
        "apparel_tailoring": 55,
        "solar_technician": 30,
        "automotive_ev": 25,
        "digital_csc": 40,
        "healthcare_assistant": 45
    }
}

def get_all_supported_states() -> List[str]:
    """Returns list of supported states for capacity tracking."""
    return list(ESTIMATED_CAPACITY_DATA.keys())

def get_capacity_for_state(state: str) -> Dict[str, int]:
    """Returns the capacity mapping for a specific state or empty dict if not found."""
    return ESTIMATED_CAPACITY_DATA.get(state, {})

def evaluate_gap(demand: int, capacity: int) -> Dict[str, Any]:
    """
    Computes the gap indicator:
    - demand_exceeding: Demand significantly exceeding capacity (Demand > Capacity * 1.15)
    - roughly_matched: Demand roughly matched with capacity (0.75 <= Ratio <= 1.15)
    - capacity_exceeding: Capacity exceeding demand (Demand < Capacity * 0.75)
    """
    if capacity <= 0:
        ratio = float("inf") if demand > 0 else 0.0
    else:
        ratio = round(demand / capacity, 2)

    diff = demand - capacity

    if demand > capacity * 1.15:
        gap_status = "demand_exceeding"
        gap_label = "Demand Significantly Exceeding Capacity"
        gap_short = "Capacity Deficit"
        color = "red"
        badge_class = "bg-[#fee2e2] text-[#991b1b] border-[#fecaca]"
        icon = "error"
    elif demand < capacity * 0.75:
        gap_status = "capacity_exceeding"
        gap_label = "Capacity Exceeding Demand"
        gap_short = "Surplus Capacity"
        color = "green"
        badge_class = "bg-[#ecfdf5] text-[#065f46] border-[#a7f3d0]"
        icon = "check_circle"
    else:
        gap_status = "roughly_matched"
        gap_label = "Roughly Matched"
        gap_short = "Balanced Capacity"
        color = "blue"
        badge_class = "bg-[#eff6ff] text-[#1e40af] border-[#bfdbfe]"
        icon = "balance"

    return {
        "status": gap_status,
        "label": gap_label,
        "short_label": gap_short,
        "color": color,
        "badge_class": badge_class,
        "icon": icon,
        "difference": diff,
        "ratio": ratio
    }

def build_capacity_gap_report(state: str, demand_by_trade: Dict[str, int]) -> Dict[str, Any]:
    """
    Constructs a full regional capacity vs demand report for a single state or 'all'.
    """
    catalog = nsqf_rules.TRADES_CATALOG
    trades_report: List[Dict[str, Any]] = []

    if state.lower() == "all":
        # Aggregate across all 5 states
        aggregated_capacity: Dict[str, int] = {}
        for s_data in ESTIMATED_CAPACITY_DATA.values():
            for t_key, cap_val in s_data.items():
                aggregated_capacity[t_key] = aggregated_capacity.get(t_key, 0) + cap_val

        for t_key, t_info in catalog.items():
            demand = demand_by_trade.get(t_key, 0)
            capacity = aggregated_capacity.get(t_key, 0)
            gap = evaluate_gap(demand, capacity)
            trades_report.append({
                "trade_key": t_key,
                "trade_name": t_info.get("trade_name", t_key),
                "qp_name": t_info.get("qp_name"),
                "qp_code": t_info.get("qp_code"),
                "nsqf_level": t_info.get("nsqf_level"),
                "ssc_name": t_info.get("ssc_name"),
                "demand": demand,
                "estimated_capacity": capacity,
                "difference": gap["difference"],
                "ratio": gap["ratio"],
                "gap_status": gap["status"],
                "gap_label": gap["label"],
                "gap_short_label": gap["short_label"],
                "gap_color": gap["color"],
                "gap_badge_class": gap["badge_class"],
                "gap_icon": gap["icon"]
            })
    else:
        state_capacity = get_capacity_for_state(state)
        for t_key, t_info in catalog.items():
            demand = demand_by_trade.get(t_key, 0)
            capacity = state_capacity.get(t_key, 0)
            gap = evaluate_gap(demand, capacity)
            trades_report.append({
                "trade_key": t_key,
                "trade_name": t_info.get("trade_name", t_key),
                "qp_name": t_info.get("qp_name"),
                "qp_code": t_info.get("qp_code"),
                "nsqf_level": t_info.get("nsqf_level"),
                "ssc_name": t_info.get("ssc_name"),
                "demand": demand,
                "estimated_capacity": capacity,
                "difference": gap["difference"],
                "ratio": gap["ratio"],
                "gap_status": gap["status"],
                "gap_label": gap["label"],
                "gap_short_label": gap["short_label"],
                "gap_color": gap["color"],
                "gap_badge_class": gap["badge_class"],
                "gap_icon": gap["icon"]
            })

    total_demand = sum(t["demand"] for t in trades_report)
    total_capacity = sum(t["estimated_capacity"] for t in trades_report)
    overall_gap = evaluate_gap(total_demand, total_capacity)

    return {
        "state": state,
        "disclaimer": CAPACITY_DISCLAIMER,
        "is_capacity_verified": False,
        "supported_states": get_all_supported_states(),
        "total_demand": total_demand,
        "total_estimated_capacity": total_capacity,
        "overall_gap": overall_gap,
        "trades": trades_report
    }
