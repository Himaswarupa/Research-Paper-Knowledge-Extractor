import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter


def read_pdf(path: str) -> str:
    doc = pymupdf.open(path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()

    idx = text.rfind("\nReferences")
    if idx > len(text) * 0.5:
        text = text[:idx]
    return text


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
    )
    return splitter.split_text(text)


if __name__ == "__main__":
    text = read_pdf("data/paper1.pdf")
    chunks = chunk_text(text)
    print(f"Total chars: {len(text)}")
    print(f"Total chunks: {len(chunks)}")
    print(chunks[0])