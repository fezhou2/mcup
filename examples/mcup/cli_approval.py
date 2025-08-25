import asyncio
from mcup.client import stdio_client
from mcup.shared.stdio import StdioServerParameters

async def main():
    server_params = StdioServerParameters(command="uv", args=["run", "server", "fastmcp_quickstart", "stdio"])
    async with stdio_client(server_params, approval_mode='cli') as session:
        # Prompts for approval (mutating tool)
        try:
            result = await session.call_tool("write_data", {"data": "example"})
            print(f"Write result: {result}")
        except Exception as e:
            print(f"Error calling write_data: {e}")
        # No prompt (non-mutating tool)
        try:
            result = await session.call_tool("get_data", {"id": "123"})
            print(f"Get result: {result}")
        except Exception as e:
            print(f"Error calling get_data: {e}")
        # No prompt (non-tool action)
        tools = await session.list_tools()
        print(f"Tools: {tools}")
        resource = await session.read_resource("file:///data/readme.txt")
        print(f"Resource: {resource}")

if __name__ == "__main__":
    asyncio.run(main())