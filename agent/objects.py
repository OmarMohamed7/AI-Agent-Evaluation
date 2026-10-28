from pydantic import BaseModel, Field

class Answer(BaseModel):
    answer: str = Field(description="The answer is needed for the user question")
    conversation: bool = Field(description="Indicator to know if the conversation should" \
        "continue or not. if the agent made the decision about the refund this should be false."\
            "if the conversation still need more talk then it's true." , default=True)
    
class PurchasItem(BaseModel):
    name: str = Field(description="Name of the item purchased")
    