"""Conversation persistence is the API's AIConversation table."""


def empty_memory() -> dict:
    return {"messages": [], "note": "Persisted by the API when a workspace is present."}
