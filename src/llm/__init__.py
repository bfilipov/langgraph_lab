from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gpt-oss:20b",
    base_url="http://localhost:11434",
)

