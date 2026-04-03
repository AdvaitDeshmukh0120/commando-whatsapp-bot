import os
import glob
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import config


def load_knowledge_base():
    documents = []

    kb_path = config.KNOWLEDGE_BASE_PATH
    if os.path.exists(kb_path):
        print(f"Loading: {kb_path}")
        with open(kb_path, 'r', encoding='utf-8') as f:
            content = f.read()

        sections = content.split("===== PAGE:")
        for section in sections:
            if section.strip():
                lines = section.strip().split('\n')
                source = "commando_knowledge_base"
                for line in lines:
                    if line.startswith("URL:"):
                        source = line.replace("URL:", "").strip()
                        break
                documents.append(Document(page_content=section.strip(), metadata={"source": source}))

    scraped_path = os.path.join("data", "scraped_website_data.txt")
    if os.path.exists(scraped_path):
        print(f"Loading: {scraped_path}")
        with open(scraped_path, 'r', encoding='utf-8') as f:
            content = f.read()
        sections = content.split("=====")
        for section in sections:
            if section.strip() and len(section.strip()) > 50:
                documents.append(Document(page_content=section.strip(), metadata={"source": "scraped_website"}))

    for txt_file in glob.glob("data/*.txt"):
        if txt_file not in [kb_path, scraped_path]:
            print(f"Loading: {txt_file}")
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.strip():
                if "===" in content:
                    sections = content.split("\n=== ")
                    for section in sections:
                        section = section.strip()
                        if section and len(section) > 30:
                            documents.append(Document(page_content=section, metadata={"source": txt_file}))
                else:
                    documents.append(Document(page_content=content, metadata={"source": txt_file}))

    print(f"\nLoaded {len(documents)} document sections.")
    return documents


def chunk_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})")
    return chunks


def build_vectorstore(chunks):
    print(f"\nLoading embedding model: {config.EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    print("Building FAISS vector store...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(os.path.dirname(config.VECTORSTORE_PATH), exist_ok=True)
    vectorstore.save_local(config.VECTORSTORE_PATH)
    print(f"Vector store saved to: {config.VECTORSTORE_PATH}")
    return vectorstore


def main():
    print("=" * 60)
    print("COMMANDO RAG - Vector Store Builder")
    print("=" * 60)

    print("\n[1/3] Loading knowledge base...")
    documents = load_knowledge_base()
    if not documents:
        print("No documents found. Check data/ directory.")
        return

    print("\n[2/3] Chunking documents...")
    chunks = chunk_documents(documents)

    print("\n[3/3] Building vector store...")
    vectorstore = build_vectorstore(chunks)

    print("\nQuick test...")
    query = "Which switches support stacking?"
    results = vectorstore.similarity_search(query, k=3)
    print(f"Query: '{query}'")
    for i, doc in enumerate(results):
        preview = doc.page_content[:120].replace('\n', ' ')
        print(f"  Result {i+1}: {preview}...")

    print("\nBuild complete!")


if __name__ == "__main__":
    main()
