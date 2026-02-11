"""Good MCP tool example — clear description, typed inputs, error handling."""

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("invoice-tools")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_invoice",
            description="Retrieve a single invoice by its UUID. Returns invoice details including customer, status, and line items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "The UUID of the invoice to retrieve",
                    },
                },
                "required": ["invoice_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_invoice":
        invoice_id = arguments.get("invoice_id")
        if not invoice_id:
            return [TextContent(type="text", text="Error: invoice_id is required")]

        try:
            invoice = await invoice_service.get(invoice_id)
            return [TextContent(type="text", text=invoice.to_json())]
        except InvoiceNotFoundError:
            return [TextContent(type="text", text=f"Invoice {invoice_id} not found")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]
