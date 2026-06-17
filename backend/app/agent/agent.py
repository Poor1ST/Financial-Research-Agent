from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.agent.tools import (
    fetch_price_and_indicators,
    fetch_price_history,
    search_financial_news,
    query_documents,
    generate_analysis_report,
)
from app.agent.prompt import SYSTEM_PROMPT
from langchain_core.tools import Tool
import os


def build_agent(session_id: str = "default", initial_messages: list[tuple[str, str]] | None = None):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.3,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    tools = [
        fetch_price_and_indicators,
        fetch_price_history,
        search_financial_news,
        query_documents,
        generate_analysis_report,
    ]

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        k=10,
        return_messages=True,
        output_key="output",
    )

    if initial_messages:
        for role, content in initial_messages:
            if role == "user":
                memory.chat_memory.add_user_message(content)
            else:
                memory.chat_memory.add_ai_message(content)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        return_intermediate_steps=True,
    )

    return agent_executor
