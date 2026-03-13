"""
FastAPI Tool Server for OpenFR.

Exposes the existing Python financial tools via HTTP endpoints,
allowing the TypeScript Agent to discover and call them.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from openfr.tools.parallel import can_parallelize, execute_tools_parallel
from openfr.tools.registry import get_all_tools

logger = logging.getLogger(__name__)

app = FastAPI(title="OpenFR Tool Server", version="0.1.0")

# Thread pool for running sync tool calls
_executor = ThreadPoolExecutor(max_workers=8)


def _build_tool_map() -> dict[str, Any]:
    """Build a name -> tool mapping from the registry."""
    tools = get_all_tools()
    return {t.name: t for t in tools}


def _get_tool_metadata(tool: Any) -> dict[str, Any]:
    """Extract metadata from a LangChain tool for the /tools endpoint."""
    from openfr.formatter import _TOOL_DISPLAY_NAMES

    meta: dict[str, Any] = {
        "name": tool.name,
        "description": tool.description or "",
        "label": _TOOL_DISPLAY_NAMES.get(tool.name, tool.name),
    }

    # Extract JSON Schema from the tool's args_schema (Pydantic model)
    if hasattr(tool, "args_schema") and tool.args_schema is not None:
        try:
            schema = tool.args_schema.model_json_schema()
            meta["parameters"] = schema
        except Exception:
            meta["parameters"] = {"type": "object", "properties": {}}
    else:
        meta["parameters"] = {"type": "object", "properties": {}}

    # Assign category
    from openfr.tools.registry import (
        FUND_TOOLS,
        FUTURES_TOOLS,
        INDEX_TOOLS,
        MACRO_TOOLS,
        STOCK_HK_TOOLS,
        STOCK_TOOLS,
    )

    name = tool.name
    stock_names = {t.name for t in STOCK_TOOLS}
    hk_names = {t.name for t in STOCK_HK_TOOLS}
    fund_names = {t.name for t in FUND_TOOLS}
    futures_names = {t.name for t in FUTURES_TOOLS}
    index_names = {t.name for t in INDEX_TOOLS}
    macro_names = {t.name for t in MACRO_TOOLS}

    if name in stock_names:
        meta["category"] = "stock"
    elif name in hk_names:
        meta["category"] = "stock_hk"
    elif name in fund_names:
        meta["category"] = "fund"
    elif name in futures_names:
        meta["category"] = "futures"
    elif name in index_names:
        meta["category"] = "index"
    elif name in macro_names:
        meta["category"] = "macro"
    else:
        meta["category"] = "other"

    return meta


# --- Endpoints ---


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tools")
async def list_tools():
    """Return metadata for all available tools."""
    tool_map = _build_tool_map()
    tools_meta = [_get_tool_metadata(t) for t in tool_map.values()]
    return {"tools": tools_meta}


class ToolCallRequest(BaseModel):
    """Request body for single tool invocation."""

    args: dict[str, Any] = {}


class BatchToolCall(BaseModel):
    name: str
    args: dict[str, Any] = {}


class BatchToolCallRequest(BaseModel):
    """Request body for batch tool invocation."""

    calls: list[BatchToolCall]


@app.post("/tools/batch")
async def call_tools_batch(request: BatchToolCallRequest):
    """Invoke multiple tools, potentially in parallel."""
    tool_map = _build_tool_map()
    calls = [{"name": c.name, "args": c.args} for c in request.calls]

    def get_tool_func(name: str):
        return tool_map.get(name)

    use_parallel = can_parallelize(calls)
    loop = asyncio.get_event_loop()

    if use_parallel:
        results = await loop.run_in_executor(
            _executor,
            execute_tools_parallel,
            calls,
            get_tool_func,
        )
    else:
        # Execute sequentially
        results = []
        for call in calls:
            t = tool_map.get(call["name"])
            if not t:
                results.append(
                    {"tool_name": call["name"], "args": call["args"], "result": None, "error": f"Tool not found: {call['name']}"}
                )
                continue
            try:
                res = await loop.run_in_executor(_executor, t.invoke, call["args"])
                results.append({"tool_name": call["name"], "args": call["args"], "result": res, "error": None})
            except Exception as e:
                results.append({"tool_name": call["name"], "args": call["args"], "result": None, "error": str(e)})

    return {"results": results}


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: ToolCallRequest):
    """Invoke a single tool by name."""
    tool_map = _build_tool_map()
    tool = tool_map.get(tool_name)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(_executor, tool.invoke, request.args)
        return {"result": result, "error": None}
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {"result": None, "error": str(e)}


def main():
    """Entry point for the openfr-server script."""
    import os

    host = os.getenv("OPENFR_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("OPENFR_SERVER_PORT", "18321"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
