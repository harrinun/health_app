from typing import List, Dict, Any, Optional


def paginate(items: List[Dict], page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    data = items[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": data
    }


def filter_items(items: List[Dict], filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
    if not filters:
        return items

    def match(item: Dict) -> bool:
        for key, value in filters.items():
            if isinstance(value, str) and value.lower() != str(item.get(key, "")).lower():
                return False
            elif isinstance(value, (int, float)) and item.get(key) != value:
                return False
        return True

    return [item for item in items if match(item)]
