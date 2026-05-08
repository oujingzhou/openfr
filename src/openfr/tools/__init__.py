"""
Tools module for OpenFR.
"""

from openfr.tools.registry import get_all_tools, get_tool_descriptions
from openfr.tools.base import format_dataframe

# 导出所有工具函数供 agents 使用
from openfr.tools.stock import (
    get_stock_realtime,
    get_stock_history,
    get_stock_info,
    get_stock_financials,
    search_stock,
    search_stock_any,
    get_stock_news,
    get_hot_stocks,
    get_industry_boards,
    get_industry_board_detail,
)
from openfr.tools.stock_ext import (
    get_stock_bid_ask,
    get_stock_fund_flow,
    get_stock_lhb_detail,
    get_stock_lhb_dates,
    get_stock_lhb_rank,
    get_stock_yjyg,
    get_stock_yjbb,
    get_stock_profit_forecast,
)
from openfr.tools.stock_hk import (
    get_stock_hk_realtime,
    get_stock_hk_history,
    search_stock_hk,
)
from openfr.tools.fund import (
    get_fund_list,
    get_etf_realtime,
    get_etf_history,
    get_fund_rank,
)
from openfr.tools.futures import (
    get_futures_realtime,
    get_futures_history,
    get_futures_inventory,
)
from openfr.tools.index import (
    get_index_realtime,
    get_index_history,
)
from openfr.tools.macro import (
    get_macro_cpi,
    get_macro_ppi,
    get_macro_pmi,
    get_macro_gdp,
    get_money_supply,
)

__all__ = [
    "get_all_tools",
    "get_tool_descriptions",
    "format_dataframe",
    # Stock tools
    "get_stock_realtime",
    "get_stock_history",
    "get_stock_info",
    "get_stock_financials",
    "search_stock",
    "search_stock_any",
    "get_stock_news",
    "get_hot_stocks",
    "get_industry_boards",
    "get_industry_board_detail",
    "get_stock_bid_ask",
    "get_stock_fund_flow",
    "get_stock_lhb_detail",
    "get_stock_lhb_dates",
    "get_stock_lhb_rank",
    "get_stock_yjyg",
    "get_stock_yjbb",
    "get_stock_profit_forecast",
    # HK Stock tools
    "get_stock_hk_realtime",
    "get_stock_hk_history",
    "search_stock_hk",
    # Fund tools
    "get_fund_list",
    "get_etf_realtime",
    "get_etf_history",
    "get_fund_rank",
    # Futures tools
    "get_futures_realtime",
    "get_futures_history",
    "get_futures_inventory",
    # Index tools
    "get_index_realtime",
    "get_index_history",
    # Macro tools
    "get_macro_cpi",
    "get_macro_ppi",
    "get_macro_pmi",
    "get_macro_gdp",
    "get_money_supply",
]

