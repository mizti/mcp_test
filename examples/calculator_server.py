# simple_calculator_server.py
from mcp.server.fastmcp import FastMCP
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# サーバーインスタンスの作成
mcp = FastMCP(
    name="calculator",
    description="簡単な算術計算を実行します。",
)

# 加算ツール
#@mcp.tool(annotations=["@mcp.tool.readonly"])
@mcp.tool()
async def add(a: float, b: float) -> float:
    """2つの数値を加算します。"""
    logger.info(f"ツール 'add' 呼び出し: a={a}, b={b}")
    result = a + b
    logger.info(f"計算結果: {result}")
    return result

# 減算ツール
#@mcp.tool(annotations=["@mcp.tool.readonly"])
@mcp.tool()
async def subtract(a: float, b: float) -> float:
    """最初の数値から2番目の数値を減算します。"""
    logger.info(f"ツール 'subtract' 呼び出し: a={a}, b={b}")
    result = a - b
    logger.info(f"計算結果: {result}")
    return result

# 乗算ツール
#@mcp.tool(annotations=["@mcp.tool.readonly"])
@mcp.tool()
async def multiply(a: float, b: float) -> float:
    """2つの数値を乗算します。"""
    logger.info(f"ツール 'multiply' 呼び出し: a={a}, b={b}")
    result = a * b
    logger.info(f"計算結果: {result}")
    return result

# 除算ツール（エラーハンドリングの例）
#@mcp.tool(annotations=["@mcp.tool.readonly"])
@mcp.tool()
async def divide(a: float, b: float) -> float:
    """最初の数値を2番目の数値で除算します。"""
    logger.info(f"ツール 'divide' 呼び出し: a={a}, b={b}")
    
    if b == 0:
        error_msg = "0による除算はできません"
        logger.error(error_msg)
        raise ValueError(error_msg)  # 適切なエラーハンドリング
    
    result = a / b
    logger.info(f"計算結果: {result}")
    return result

if __name__ == "__main__":
    logger.info("シンプルな電卓MCPサーバー (Stdio) を起動します...")
    mcp.run()
