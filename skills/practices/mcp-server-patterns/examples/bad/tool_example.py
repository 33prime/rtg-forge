"""BAD MCP tool example — vague description, no validation, no error handling."""

from mcp.server import Server

server = Server("tools")


@server.list_tools()
async def list_tools():
    return [
        {
            "name": "do_stuff",  # Vague name
            "description": "Does stuff with invoices",  # Vague description
            "inputSchema": {
                "type": "object",
                "properties": {
                    "data": {"type": "string"},  # Vague parameter name, no description
                },
            },
        },
    ]


@server.call_tool()
async def call_tool(name, arguments):
    # No input validation
    # No error handling
    result = db.query(arguments["data"])  # Could crash
    return [{"type": "text", "text": str(result)}]
