from dotenv import load_dotenv
from langchain_groq.chat_models import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7
)

response = llm.invoke([HumanMessage(content="Hello! How fast can you respond?")])

print(response)