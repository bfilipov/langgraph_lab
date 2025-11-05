from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

llm = ChatOllama(
    model="gpt-oss:20b",
    base_url="http://localhost:11434",
)

embeddings = OllamaEmbeddings(
    model="mxbai-embed-large:335m",
    base_url="http://localhost:11434",
)
