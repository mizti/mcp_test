from mcp.server.fastmcp import FastMCP
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name = "prime-checker",
    description = "与えられた整数が素数かどうかを判定します。",
)

#@mcp.tool(annotations=["@mcp.tool.readonly"]) # まだannotationsは実装されていない
@mcp.tool() 
async def is_prime(number: int) -> bool:
    """
    与えられた整数が素数かどうかを判定します。

    Args:
        number (int): 判定する整数

    Returns:
        bool: 素数ならTrue、そうでなければFalse
    """
    logger.info(f"Received number: {number}")
    if number < 2:
        return False
    for i in range(2, int(number ** 0.5) + 1):
        if number % i == 0:
            return False
    return True

@mcp.resource("prime://{number}")
async def check_prime(number: int) -> bool:
    """
    与えられた整数が素数かどうかを判定します。

    Args:
        number (int): 判定する整数

    Returns:
        bool: 素数ならTrue、そうでなければFalse
    """
    logger.info(f"Received number: {number}")
    return await is_prime(number)

if __name__ == "__main__":
    logger.info("Starting the FastMCP server(STDIO)...")
    mcp.run()