

def get_attributes(obj, max_depth=0, indent=0, visited=None)->str:
    """Recursively prints attributes of an object, handling nested objects."""
    if visited is None:
        visited = set()
    if max_depth<0: return
    s=''

    if id(obj) in visited:  # Avoid infinite loops with circular references
        s += " " * indent + f"<Already visited: {obj}>" + '\n'
        return

    visited.add(id(obj))

    for attr in dir(obj):
        if attr.startswith("__"):  # Ignore special methods
            continue
        if attr.startswith("_"):  # Ignore special methods
            continue

        try:
            value = getattr(obj, attr)
            if isinstance(value, (int, float, str, bool, type(None))):
                s += " " * indent + f"{attr}: {value}" + "\n"
            elif isinstance(value, (list, tuple, set)):
                s += " " * indent + f"{attr}: {type(value).__name__} (length {len(value)})" + "\n"
                for item in value:
                    s += get_attributes(item, max_depth - 1, indent + 4, visited)
            elif isinstance(value, dict):
                s += " " * indent + f"{attr}: dict (length {len(value)})" + "\n"
                for k, v in value.items():
                    s += " " * (indent + 4) + f"{k}:" + "\n"
                    s += get_attributes(v, max_depth - 1, indent + 8, visited)
            else:
                s += " " * indent + f"{attr}: {type(value).__name__}" + "\n"
                s += get_attributes(value, max_depth - 1, indent + 4, visited)
        except Exception as e:
            s += " " * indent + f"{attr}: <Error retrieving value: {e}>" + "\n"
    return s

