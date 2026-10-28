from langchain.tools import tool
from agent.error_model import Error
from data import users_data
from dotenv import load_dotenv
import logging
from objects import PurchasItem
from datetime import date

load_dotenv()

def get_user(user: str) -> dict | None:
    return users_data.get(user)

@tool
def get_user_purchase_history(user_id: str) -> dict | Error:
    """
    This tool takes the user username and return dictionary of 
    the user purchase history if the user exists
    """
    
    logging.info(f"Using get_user_purchase_history tool to get the user {user_id} purchases")
    
    existsUser = get_user(user_id)
    
    if existsUser:
        return existsUser;
    
    return Error(error=f"User {user_id} not found")

@tool 
def calculate_right_refund(user_id: str, items: list[PurchasItem]) -> str | Error:
    '''
    this tool takes a list of items wanted to be returned and user id and
    will return how much the refund
    '''
    
    logging.info(f"using calculate_right_refund tool to get user's : {user_id} refund")
    
    user = get_user(user_id)
    
    if not user:
        return Error(error=f"User {user_id} not found")
    
    total_refund = 0
    
    for item in items:
        if user.get(item.name):
            total_refund += user[item.name]["total_price"]
            
    return f"the value of refund is : {total_refund}"
    
    
@tool
def issue_refund_ticket(user_id: str, refund_amount: int) -> str:
    '''
    This tool will send a ticket to the right team to return the refund
    '''
    
    logging.info(f"using issue_refund_ticket for user: {user_id}")
    
    return f"a refund ticket has been issued successfully with the amout of {refund_amount}"
    
@tool
def get_today_date()-> str:
    '''
    This tool will return today's date 
    '''
    
    logging.info(f"using the date tool")
    
    return str(date.today())

