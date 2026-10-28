from langchain.tools import tool
from db.db import DB
from agent.error_model import Error
from agent.objects import PurchasItem
from dotenv import load_dotenv
import logging
from datetime import date

load_dotenv()


@tool
def get_user_purchase_history(user_id: str) -> dict | Error:
    """
    This tool takes the user id or email and returns a dictionary of
    the user purchase history if the user exists
    """

    logging.info(f"Using get_user_purchase_history tool to get the user {user_id} purchases")

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


@tool
def calculate_right_refund(user_id: str, items: list[PurchasItem]) -> str | Error:
    '''
    this tool takes a list of items wanted to be returned and user id and
    will return how much the refund
    '''

    logging.info(f"using calculate_right_refund tool to get user's : {user_id} refund")

    user = DB.get_user(user_id)

    if not user:
        return Error(error=f"User {user_id} not found")

    wanted = {item.name.lower() for item in items}
    total_refund = sum(
        p["total_price"] for p in DB.get_user_orders(user["Id"]) if p["name"].lower() in wanted
    )

    return f"the value of refund is : {total_refund}"


@tool
def issue_refund_ticket(user_id: str, refund_amount: int) -> str:
    '''
    This tool will send a ticket to the right team to return the refund
    '''

    logging.info(f"using issue_refund_ticket for user: {user_id}")

    return f"a refund ticket has been issued successfully with the amout of {refund_amount}"


@tool
def get_today_date() -> str:
    '''
    This tool will return today's date
    '''

    logging.info("using the date tool")

    return str(date.today())
