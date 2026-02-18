"""for converting data to parquet responses."""
import io
import json

import pandas as pd
from fastapi.responses import StreamingResponse


def flatten_record(record: dict) -> dict:
    """flatten nested dict or list into JSON strings for flat parquet cols. scalar values are kept as-is."""
    flat = {}
    for key, value in record.items():
        if isinstance(value, (dict, list)):
            flat[key] = json.dumps(value)
        else:
            flat[key] = value
    return flat


def parquet_response(data: list[dict], filename: str) -> StreamingResponse:
    """convert a list of dicts to a parquet file. uses zstd compression."""
    flat_data = [flatten_record(r) for r in data]
    df = pd.DataFrame(flat_data)

    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", compression="zstd", index=False)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.apache.parquet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
