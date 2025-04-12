import asyncio
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

async def run():
    server_params = StdioServerParameters(
        command="python",
        args=["prime_check_server.py"],
    )

    async def sampling_callback(message: types.CreateMessageRequestParams) -> types.CreateMessageRequest:
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text="Dummy response"
            ),
            model="gpt-3.5-turbo",
            stopReason="endTurn"
        )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=sampling_callback) as session:
            await session.initialize()

            number_to_test = 19
            tool_result = await session.call_tool("is_prime", arguments={"number": number_to_test})
            print(f"Tool result for is_prime({number_to_test}): {tool_result.content[0].text}")

            resource_uri = f"prime://{number_to_test}"
            resource_result = await session.read_resource(resource_uri)
            print(f"Resource result for {resource_uri}: {resource_result.contents[0].text}")

if __name__ == "__main__":
    asyncio.run(run())
