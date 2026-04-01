import hashlib
import os
from pathlib import Path

import chromadb
import click
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / "envs" / "local.env")

EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", default="gemini-embedding-001")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md"})
CHROMA_PERSIST_DIR = "chroma_db"


def _collect_files(path: Path) -> list[Path]:
    """Collect files with supported extensions from the given path."""
    if path.is_file():
        return [path] if path.suffix in SUPPORTED_EXTENSIONS else []

    files = sorted(
        [f for f in path.rglob("*") if f.is_file() and f.suffix in SUPPORTED_EXTENSIONS]
    )
    return files


def _file_path_hash(relative_path: str) -> str:
    """Generate a SHA256 hash of the file path (first 16 chars)."""
    hash_digest = hashlib.sha256(relative_path.encode()).hexdigest()
    return hash_digest[:16]


def _build_doc_id(file_hash: str, chunk_idx: int) -> str:
    """Build a document ID with file hash, chunk size, chunk index, and model ID."""
    return f"{file_hash}--{CHUNK_SIZE}--{chunk_idx:05d}--{EMBEDDING_MODEL_ID}"


def _ingest_file(
    file_path: Path,
    splitter: RecursiveCharacterTextSplitter,
    embeddings: GoogleGenerativeAIEmbeddings,
    collection: chromadb.Collection,
) -> int:
    """Ingest a single file into the collection."""
    content = file_path.read_text(encoding="utf-8")
    chunks = splitter.split_text(content)

    # Get relative path
    try:
        relative_path = str(file_path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        relative_path = str(file_path.resolve())

    file_hash = _file_path_hash(relative_path)

    # Generate embeddings
    vectors = embeddings.embed_documents(chunks)

    # Build metadata and IDs
    ids = [_build_doc_id(file_hash, i) for i in range(len(chunks))]
    metadatas = [
        {
            "file_name": file_path.name,
            "embedding_model": EMBEDDING_MODEL_ID,
        }
        for _ in chunks
    ]

    # Upsert into collection
    collection.upsert(
        ids=ids,
        embeddings=vectors,  # type: ignore[arg-type]
        documents=chunks,
        metadatas=metadatas,  # type: ignore[arg-type]
    )

    return len(chunks)


@click.command()
@click.option(
    "--path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to file or directory to ingest",
)
@click.option(
    "--collection",
    default="corpus",
    help="Collection name in ChromaDB",
)
def registry(path: Path, collection: str) -> None:
    """Ingest corpus into ChromaDB using Google Gemini embeddings."""
    click.echo(f"Initializing embeddings model: {EMBEDDING_MODEL_ID}")
    embeddings = GoogleGenerativeAIEmbeddings(model=f"models/{EMBEDDING_MODEL_ID}")

    click.echo(
        f"Initializing text splitter: chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}"
    )
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    click.echo(f"Connecting to ChromaDB at {CHROMA_PERSIST_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    col = client.get_or_create_collection(name=collection)

    files = _collect_files(path)
    click.echo(f"Found {len(files)} file(s) to ingest")

    total_chunks = 0
    for file_path in files:
        chunks = _ingest_file(file_path, splitter, embeddings, col)
        click.echo(f"  Ingested {file_path.name}: {chunks} chunks")
        total_chunks += chunks

    click.echo(
        f"Completed: {len(files)} file(s), {total_chunks} chunk(s) ingested into"
        f" '{collection}'"
    )


if __name__ == "__main__":
    registry()
