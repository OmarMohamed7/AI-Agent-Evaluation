from agent.models import llm
from agent.tools import all_tools

from dotenv import load_dotenv

load_dotenv()
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from agent.prompts import agent_system_prompt
from agent.objects import AgentContext, Answer
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from uuid import uuid4

agent = create_agent(
    model=llm,
    system_prompt=agent_system_prompt,
    tools=all_tools,
    response_format=ToolStrategy(Answer),
    context_schema=AgentContext,
    checkpointer=InMemorySaver(),
)


def run_conversation(user_id: str):
    context = AgentContext(user_id=user_id)
    configration = {"configurable": {"thread_id": str(uuid4())}}

    question = HumanMessage(content="I would like to refund my order")

    conversation = True

    while conversation:
        response = agent.invoke(
            {"messages": [question]}, config=configration, context=context
        )

        structured_response = response["structured_response"]

        print(structured_response.answer)

        conversation = structured_response.conversation

        if conversation:
            user_input = str(input("reply: \n"))
            question = HumanMessage(content=user_input)

    print("Job is done!")
