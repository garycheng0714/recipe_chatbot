from uuid import uuid5, NAMESPACE_DNS


def create_canonical_id(
    entity: str,
    *parts: str | int,
) -> str:
    key = ":".join([entity, *map(str, parts)])
    return str(uuid5(NAMESPACE_DNS, key))