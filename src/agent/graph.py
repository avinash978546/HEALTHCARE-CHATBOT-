from __future__ import annotations
import os
from typing import Annotated, Dict, List, Literal, TypedDict
from dotenv import load_dotenv
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph, add_messages
load_dotenv()


class Configuration(TypedDict):
    """Configurable parameters for the healthcare agent."""
    groq_api_key: str
    model_name: str




class State(TypedDict):
    """State for the healthcare chatbot agent."""
    messages: Annotated[List[BaseMessage], add_messages]





HEALTHCARE_SYSTEM_PROMPT = """Your name is JARVIS and you are a professional healthcare expert with extensive experience in clinical medicine, 
diagnostics, and patient education. Your role is to provide clear, accurate, and responsible health 
information based on the latest medical guidelines and evidence-based practices. You are also a certified nutritionist 
who provides personalized diet recommendations when users ask about food, nutrition, or diet plans.

Always clarify that your advice does not replace a consultation with a licensed physician or dietitian. 
Respond with empathy, professionalism, and clarity, suitable for people of all ages and backgrounds. 
When needed, ask follow-up questions to ensure the best possible guidance.

You are made by AVINASH."""


def extract_text_content(content) -> str:
    """Extracts text from message content that can be string or list of strings/dicts."""
    if isinstance(content, list):
        text = ""
        for item in content:
            if isinstance(item, dict) and "text" in item:
                text += item["text"] + " "
            elif isinstance(item, str):
                text += item + " "
        return text.strip()
    elif isinstance(content, str):
        return content.strip()
    else:
        return ""

def setup_llm(config: RunnableConfig) -> ChatGroq:
    """Initialize the LLM with configuration."""
    configuration = config.get("configurable", {})
    api_key = configuration.get("groq_api_key") or os.getenv("GROQ_API_KEY")
    model_name = configuration.get("model_name", "llama3-8b-8192")

    if not api_key:
        raise ValueError("GROQ_API_KEY must be provided in configuration or environment variables")

    return ChatGroq(
        model_name=model_name,
        groq_api_key=api_key
    )

def route_user_input(state: State) -> Literal["chatbot_agent", "wiki_search_agent"]:
    """Route user input to appropriate agent based on content."""
    if not state["messages"]:
        return "chatbot_agent"

    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        user_input = extract_text_content(last_message.content).lower()

        wiki_keywords = ["history", "wiki", "explain", "information about", "tell me about"]
        if any(keyword in user_input for keyword in wiki_keywords):
            return "wiki_search_agent"

    return "chatbot_agent"




def chatbot_agent(state: State, config: RunnableConfig) -> Dict[str, List[BaseMessage]]:
    """Healthcare chatbot agent that provides medical and nutritional advice."""
    if not state["messages"]:
        return {"messages": [AIMessage(content="Hello! I'm JARVIS, your healthcare assistant. How can I help you today?")]}

    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        llm = setup_llm(config)

        prompt = ChatPromptTemplate.from_messages([
            ("system", HEALTHCARE_SYSTEM_PROMPT),
            ("human", "{input}")
        ])


        chain = prompt | llm
        response = chain.invoke({"input": extract_text_content(last_message.content)})

        return {"messages": [AIMessage(content=response.content)]}

    return {"messages": []}

def wiki_search_agent(state: State, config: RunnableConfig) -> Dict[str, List[BaseMessage]]:
    """Wikipedia search agent for general information queries."""
    if not state["messages"]:
        return {"messages": [AIMessage(content="I need a query to search Wikipedia.")]}

    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        try:
            wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

            query = extract_text_content(last_message.content)
            result = wiki_tool.run(query)

            if "\nSummary:" in result:
                cleaned = result.split("\nSummary:")[1].split("\n")[0].strip()
            else:
                cleaned = result.strip()

            if len(cleaned) > 1000:
                cleaned = cleaned[:1000] + "..."

            response_content = f"Here's what I found about '{query}':\n\n{cleaned}\n\nIf you have any health-related questions about this topic, I'm here to help!"

            return {"messages": [AIMessage(content=response_content)]}

        except Exception as e:
            error_message = f"I apologize, but I couldn't retrieve information about '{extract_text_content(last_message.content)}' at the moment. Please try rephrasing your question or ask me about health and nutrition topics directly."
            return {"messages": [AIMessage(content=error_message)]}

    return {"messages": []}
#graph 
graph = StateGraph(State, config_schema=Configuration)
graph.add_node("chatbot_agent", chatbot_agent)
graph.add_node("wiki_search_agent", wiki_search_agent)

# Define the start and end nodes



















































































































































graph.add_conditional_edges(
    START,
    route_user_input,
    {
        "chatbot_agent": "chatbot_agent",
        "wiki_search_agent": "wiki_search_agent"
    }
)


graph.add_edge("chatbot_agent", END)
graph.add_edge("wiki_search_agent", END)

# Compile the graph
graph = graph.compile(name="Healthcare JARVIS Agent")
