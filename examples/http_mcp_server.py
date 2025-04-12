# http_mcp_server.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional, Union

# FastAPIアプリの設定
app = FastAPI(title="MCP HTTP Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JSON-RPCリクエストモデル
class JsonRpcRequest(BaseModel):
    jsonrpc: str
    id: Optional[int] = None
    method: str
    params: Dict = {}

# 利用可能なツール定義
available_tools = {
    "calculator/add": {
        "name": "calculator/add",
        "description": "Add two numbers together",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        },
        "annotations": ["@mcp.tool.readonly"]
    },
    "datetime/now": {
        "name": "datetime/now",
        "description": "Get current date and time",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {"type": "string", "description": "Output format (optional)"}
            }
        },
        "annotations": ["@mcp.tool.readonly"]
    }
}

# ツール実装
async def execute_tool(tool_name: str, params: dict) -> dict:
    """ツール名とパラメータに基づいて実行処理を行う関数"""
    logger.info(f"ツール実行: {tool_name}, パラメータ: {params}")
    
    if tool_name == "calculator/add":
        if "a" not in params or "b" not in params:
            raise ValueError("Parameters 'a' and 'b' are required")
        return {"result": params["a"] + params["b"]}
    
    elif tool_name == "datetime/now":
        format_str = params.get("format", "%Y-%m-%d %H:%M:%S")
        try:
            return {"datetime": datetime.now().strftime(format_str)}
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {str(e)}")
    
    raise ValueError(f"Unknown tool: {tool_name}")

# メッセージハンドラ
async def handle_message(message: JsonRpcRequest) -> dict:
    """JSON-RPCメッセージを処理する関数"""
    try:
        if message.method == "initialize":
            # 初期化リクエスト処理
            return {
                "jsonrpc": "2.0",
                "id": message.id,
                "result": {
                    "serverInfo": {"name": "mcp-http-server", "version": "1.0.0"},
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": True}
                }
            }
        elif message.method == "tools/list":
            # ツール一覧を返す
            return {
                "jsonrpc": "2.0",
                "id": message.id,
                "result": {"tools": list(available_tools.values())}
            }
        elif message.method == "tools/call":
            # ツール呼び出し処理
            tool_name = message.params.get("toolName")
            inputs = message.params.get("inputs", {})
            
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": message.id,
                    "error": {"code": -32602, "message": "Missing required parameter: toolName"}
                }
            
            try:
                result = await execute_tool(tool_name, inputs)
                return {
                    "jsonrpc": "2.0",
                    "id": message.id,
                    "result": result
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": message.id,
                    "error": {"code": -32000, "message": str(e)}
                }
        else:
            # 未知のメソッド
            return {
                "jsonrpc": "2.0",
                "id": message.id,
                "error": {"code": -32601, "message": f"Method not found: {message.method}"}
            }
    except Exception as e:
        # 予期しないエラー
        logger.exception("メッセージ処理中にエラーが発生")
        return {
            "jsonrpc": "2.0",
            "id": message.id,
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
        }

# MCP HTTPエンドポイント
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCPリクエストを処理するエンドポイント"""
    client_id = id(request)
    logger.info(f"新しい接続: client_id={client_id}")
    
    async def process_messages():
        """受信メッセージを処理してレスポンスを生成するジェネレーター"""
        try:
            async for chunk in request.stream():
                if not chunk:
                    continue
                
                try:
                    data = json.loads(chunk.decode("utf-8"))
                    logger.debug(f"受信データ: {data}")
                    
                    # バッチリクエスト処理
                    if isinstance(data, list):
                        logger.info(f"バッチリクエスト処理: {len(data)}件")
                        responses = []
                        for item in data:
                            req = JsonRpcRequest(**item)
                            resp = await handle_message(req)
                            responses.append(resp)
                        yield json.dumps(responses).encode("utf-8") + b"\n"
                    else:
                        req = JsonRpcRequest(**data)
                        resp = await handle_message(req)
                        yield json.dumps(resp).encode("utf-8") + b"\n"
                
                except json.JSONDecodeError:
                    logger.error("JSONパースエラー")
                    error_resp = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"}
                    }
                    yield json.dumps(error_resp).encode("utf-8") + b"\n"
        except Exception as e:
            logger.exception("ストリーム処理中にエラーが発生")
            error_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Stream processing error: {str(e)}"}
            }
            yield json.dumps(error_resp).encode("utf-8") + b"\n"
        finally:
            logger.info(f"接続終了: client_id={client_id}")
    
    return StreamingResponse(
        process_messages(),
        media_type="application/x-ndjson"
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("MCP HTTPサーバーを起動します...")
    uvicorn.run(app, host="0.0.0.0", port=8080)