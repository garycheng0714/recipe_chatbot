import uuid

NS = uuid.uuid5(uuid.NAMESPACE_URL, "rag-pipeline")

def get_source_id(url: str) -> uuid.UUID:
    return uuid.uuid5(NS, url)

def get_section_id(source_id: uuid.UUID, order_index: int) -> uuid.UUID:
    return uuid.uuid5(NS, f"{source_id}:section:{order_index}")

def chunk_id(section_id: uuid.UUID, order_index: int) -> uuid.UUID:
    return uuid.uuid5(NS, f"{section_id}:chunk:{order_index}")

def translation_id(chunk_id: uuid.UUID, language: str) -> uuid.UUID:
    return uuid.uuid5(NS, f"{chunk_id}:translation:{language}")

def embedding_run_id(chunk_id: uuid.UUID, model: str, source_field: str) -> uuid.UUID:
    return uuid.uuid5(NS, f"{chunk_id}:embedding:{model}:{source_field}")