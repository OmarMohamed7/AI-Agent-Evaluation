from dotenv import load_dotenv

load_dotenv()
from langchain.tools import tool, ToolRuntime
from db.db import DB
from agent.error_model import Error
from agent.objects import AgentContext, PurchasItem
import logging
from datetime import date, datetime, timedelta, timezone

REFUND_WINDOW_DAYS = 30

# (user_id, items) pairs that already got a ticket, to block duplicates.
_issued_tickets: set[tuple[int, frozenset[str]]] = set()


def purchase_history(user_id: str) -> dict | Error:
    user = DB.get_user(user_id)

    if not user:
        return Error(error=f"User {user_id} not found")

    purchases = [
        {
            "order_id": p["order_id"],
            "item": p["name"],
            "price": float(p["price"]),
            "quantity": p["quantity"],
            "total_price": float(p["total_price"]),
            "date": p["date"].date().isoformat(),
            "status": p["status"],
        }
        for p in DB.get_user_orders(user["Id"])
    ]

    return {"user": user["Name"], "purchases": purchases}


def _requested_orders(user: dict, items: list[PurchasItem]) -> list[dict]:
    wanted = {item.name.lower() for item in items}
    return [p for p in DB.get_user_orders(user["Id"]) if p["name"].lower() in wanted]


@tool
def get_user_purchase_history(runtime: ToolRuntime[AgentContext]) -> dict | Error:
    """
    Returns the purchase history of the current authenticated customer.
    """

    user_id = runtime.context.user_id
    logging.info(
        f"Using get_user_purchase_history tool to get the user {user_id} purchases"
    )

    return purchase_history(user_id)


@tool
def calculate_right_refund(
    items: list[PurchasItem], runtime: ToolRuntime[AgentContext]
) -> str | Error:
    """
    this tool takes a list of items wanted to be returned and will return
    how much the refund is for the current authenticated customer
    """

    user_id = runtime.context.user_id
    logging.info(f"using calculate_right_refund tool to get user's : {user_id} refund")

    user = DB.get_user(user_id)

    if not user:
        return Error(error=f"User {user_id} not found")

    total_refund = sum(p["total_price"] for p in _requested_orders(user, items))

    return f"the value of refund is : {total_refund}"


@tool
def issue_refund_ticket(
    items: list[PurchasItem], refund_amount: int, runtime: ToolRuntime[AgentContext]
) -> str | Error:
    """
    This tool will send a ticket to the right team to return the refund for
    the current authenticated customer. The amount must match the verified refund.
    """

    user_id = runtime.context.user_id
    logging.info(f"using issue_refund_ticket for user: {user_id}")

    user = DB.get_user(user_id)

    if not user:
        return Error(error=f"User {user_id} not found")

    if refund_amount <= 0:
        return Error(error="Refund amount must be positive")

    cutoff = datetime.now(timezone.utc) - timedelta(days=REFUND_WINDOW_DAYS)
    eligible = [
        p
        for p in _requested_orders(user, items)
        if cutoff <= p["date"] <= datetime.now(timezone.utc)
    ]

    if not eligible:
        return Error(
            error=f"No matching purchase within the last {REFUND_WINDOW_DAYS} days"
        )

    verified_amount = sum(p["total_price"] for p in eligible)
    if refund_amount != verified_amount:
        return Error(error="Refund amount does not match the verified purchase amount")

    key = (user["Id"], frozenset(item.name.lower() for item in items))
    if key in _issued_tickets:
        return Error(error="A refund ticket was already issued for these items")
    _issued_tickets.add(key)

    return f"a refund ticket has been issued successfully with the amout of {refund_amount}"


@tool
def get_today_date() -> str:
    """
    This tool will return today's date
    """

    logging.info("using the date tool")

    return str(date.today())


all_tools = [
    get_user_purchase_history,
    calculate_right_refund,
    issue_refund_ticket,
    get_today_date,
]

all_tools_names = [str(tool.name) for tool in all_tools]
