from typing import List, Dict
from django.db.backends.utils import CursorWrapper


def dictfetchall(cursor: CursorWrapper) -> List[Dict[str, object]]:
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

