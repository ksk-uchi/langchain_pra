import os
from pathlib import Path
from typing import Any

import chromadb
import click
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / "envs" / "local.env")

EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", default="gemini-embedding-001")
QUERY_MODEL_ID = os.getenv("QUERY_MODEL_ID", default="gemini-2.5-flash")
CHROMA_PERSIST_DIR = "chroma_db"


@click.command()
@click.option(
    "--query",
    required=True,
    type=str,
    help="Text to query the LLM",
)
@click.option(
    "--collection",
    default=None,
    type=str,
    help="ChromaDB collection name for RAG",
)
@click.option(
    "--n",
    default=5,
    type=int,
    help="Number of documents to retrieve from RAG",
)
def query(query: str, collection: str | None, n: int) -> None:
    """Query the LLM with optional RAG support from ChromaDB."""
    llm = ChatGoogleGenerativeAI(model=QUERY_MODEL_ID)

    if collection is None:
        # RAG なし: シンプルなプロンプト
        prompt = ChatPromptTemplate.from_template("{query}")
        simple_chain = prompt | llm | StrOutputParser()
        result = simple_chain.invoke({"query": query})
        click.echo(result)
    else:
        # RAG あり: コンテキスト付きプロンプト
        embeddings = GoogleGenerativeAIEmbeddings(model=f"models/{EMBEDDING_MODEL_ID}")
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        vectorstore = Chroma(
            client=client,
            collection_name=collection,
            embedding_function=embeddings,
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": n})

        prompt_template = ChatPromptTemplate.from_template(
            """以下のコンテキストを参考に、質問に答えてください。

コンテキスト:
{context}

質問: {question}"""
        )

        def format_docs(docs: list[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain: Any = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough(),
            }
            | prompt_template
            | llm
            | StrOutputParser()
        )

        result = rag_chain.invoke(query)
        click.echo(result)


if __name__ == "__main__":
    query()
