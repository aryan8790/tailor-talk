"""
LangChain conversational agent with a DriveSearchTool.
Uses direct tool-calling loop (no AgentExecutor) for compatibility
with newer LangChain versions.
"""

import os
import json
import logging
from typing import Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from drive_service import search_files, format_files_for_display

logger = logging.getLogger(__name__)

# ─── Tool ────────────────────────────────────────────────────────────────────

class DriveSearchInput(BaseModel):
    query: str = Field(
        description=(
            "A valid Google Drive API `q` (query) parameter string. "
            "Examples: name = 'budget.xlsx', name contains 'report', "
            "mimeType = 'application/pdf', fullText contains 'revenue', "
            "modifiedTime > '2024-01-01T00:00:00'"
        )
    )
    max_results: int = Field(default=10, ge=1, le=20)


class DriveSearchTool(BaseTool):
    name: str = "drive_search"
    description: str = (
        "Search for files inside the designated Google Drive folder. "
        "Translate the user's natural language request into a Drive API query string. "
        "Use this tool for ANY request about finding, listing, or filtering files."
    )
    args_schema: type[BaseModel] = DriveSearchInput

    def _run(self, query: str, max_results: int = 10) -> str:
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        try:
            files = search_files(query=query, folder_id=folder_id, max_results=max_results)
            return format_files_for_display(files)
        except Exception as e:
            logger.error("DriveSearchTool error: %s", e)
            return f"Error searching Drive: {e}"

    async def _arun(self, query: str, max_results: int = 10) -> str:
        return self._run(query, max_results)


SYSTEM_PROMPT = """You are DriveBot, a helpful assistant for finding files in Google Drive.

Google Drive query syntax:
- Exact name: name = 'file.pdf'
- Partial name: name contains 'budget'
- PDF: mimeType = 'application/pdf'
- Google Doc: mimeType = 'application/vnd.google-apps.document'
- Google Sheet: mimeType = 'application/vnd.google-apps.spreadsheet'
- Images: mimeType contains 'image/'
- Text search: fullText contains 'revenue'
- By date: modifiedTime > '2024-01-01T00:00:00'
- Combined: name contains 'report' and mimeType = 'application/pdf'

Always use the drive_search tool when the user asks to find or list files.
Present results clearly and offer to refine the search."""

_TOOLS = [DriveSearchTool()]
_TOOL_MAP = {t.name: t for t in _TOOLS}
_llm_with_tools = None


def _get_llm_with_tools():
    global _llm_with_tools
    if _llm_with_tools is None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
        elif provider == "groq":
            from langchain_groq import ChatGroq
            llm = ChatGroq(model=os.getenv("GROQ_MODEL", "llama3-70b-8192"), temperature=0)
        elif provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"), temperature=0)
        else:
            raise ValueError(f"Unknown LLM_PROVIDER '{provider}'")
        _llm_with_tools = llm.bind_tools(_TOOLS)
    return _llm_with_tools


def chat(user_message: str, history: list[dict]) -> str:
    llm = _get_llm_with_tools()
    messages: list[Any] = [SystemMessage(content=SYSTEM_PROMPT)]

    for turn in history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        elif turn["role"] == "assistant":
            messages.append(AIMessage(content=turn["content"]))

    messages.append(HumanMessage(content=user_message))

    for _ in range(5):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content or "I could not generate a response."

        for tool_call in response.tool_calls:
            result = _TOOL_MAP[tool_call["name"]]._run(**tool_call["args"])
            messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

    return "Maximum steps reached. Please try a simpler query."
