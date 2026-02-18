import hashlib
import json as json_mod
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import String, DateTime, Index, UUID, ForeignKey, BigInteger, Integer, Text, text, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.config import settings
from app.dependencies import AsyncDatabase
from app.models import Base
from app.modules.authentication import User, fastapi_users


################################################################################
# helpers
def date_to_epoch_ms(date_str: str) -> int:
    """Convert YYYY-MM-DD string to epoch milliseconds (start of day UTC)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


_SAFE_IDENTIFIER_RE = re.compile(r'^[a-zA-Z0-9_x-]+$')


def _validate_identifier(value: str) -> str:
    """Validate a filter value contains only safe characters for SQL interpolation."""
    if not _SAFE_IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid filter value: {value}")
    return value


def _validate_uuid(value: str) -> str:
    """Validate and return a UUID string."""
    uuid.UUID(value)  # raises ValueError if invalid
    return value


################################################################################
# model
class GeneratedExport(Base):
    """tracks generated parquet export files for deduplication.
    if the same query is requested again, serves the cached file.
    """
    __tablename__ = "generated_export"
    __table_args__ = (
        Index("idx_generated_export_query_hash", "query_hash", unique=True),
        Index("idx_generated_export_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, server_default=text("uuidv7()"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    # query identity
    query_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    filters_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    sql_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # file info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compression: Mapped[str] = mapped_column(String(16), default="zstd", nullable=False)

    # who created it
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )


################################################################################
# service
class DataExportService:
    """service for managing cached export files."""

    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.export_dir = Path(settings.EXPORT_DIR)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def hash_query(full_sql: str) -> str:
        """sha256 hash of the full sql query."""
        return hashlib.sha256(full_sql.encode()).hexdigest()

    async def get_cached_export(self, query_hash: str) -> Optional[GeneratedExport]:
        """look up a cached export by query hash. Returns None if not found or file missing."""
        result = await self.db.execute(
            select(GeneratedExport).where(GeneratedExport.query_hash == query_hash)
        )
        export = result.scalar_one_or_none()
        if export and os.path.exists(export.file_path):
            return export
        return None

    async def create_export(
        self,
        df: pd.DataFrame,
        query_hash: str,
        filters_json: Optional[dict] = None,
        sql_query: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        filename_prefix: str = "export",
    ) -> GeneratedExport:
        """write df to parquet, save metadata, return GeneratedExport."""
        export_id = uuid.uuid4()
        filename = f"{filename_prefix}_{export_id}.parquet"
        file_path = str(self.export_dir / filename)

        # write parquet with zstd compression
        df.to_parquet(file_path, engine="pyarrow", compression="zstd", index=False)
        file_size = os.path.getsize(file_path)

        export = GeneratedExport(
            query_hash=query_hash,
            filters_json=filters_json,
            sql_query=sql_query,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            row_count=len(df),
            compression="zstd",
            created_by_user_id=user_id,
        )
        self.db.add(export)
        await self.db.commit()
        await self.db.refresh(export)
        return export

    @staticmethod
    def file_response(export: GeneratedExport) -> FileResponse:
        """Return a FileResponse for a cached export file."""
        return FileResponse(
            path=export.file_path,
            filename=export.filename,
            media_type="application/vnd.apache.parquet",
        )


################################################################################
# cte builder
class SqlQueryRequest(BaseModel):
    """request body for sql query execution."""
    sql: str
    puzzle_types: Optional[List[str]] = None
    puzzle_sizes: Optional[List[str]] = None
    puzzle_difficulties: Optional[List[str]] = None
    user_type: Optional[str] = None
    filter_user_id: Optional[str] = None
    filter_device_id: Optional[str] = None
    solved_filter: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None


def build_base_cte(filters: SqlQueryRequest) -> str:
    """Build CTEs for 'puzzle' and 'freeplay_puzzle_attempt', filtered by sidebar selections."""
    puzzle_conditions = ["is_active = true"]

    if filters.puzzle_types:
        validated = [_validate_identifier(t) for t in filters.puzzle_types]
        types_str = ", ".join(f"'{t}'" for t in validated)
        puzzle_conditions.append(f"puzzle_type IN ({types_str})")

    if filters.puzzle_sizes:
        validated = [_validate_identifier(s) for s in filters.puzzle_sizes]
        sizes_str = ", ".join(f"'{s}'" for s in validated)
        puzzle_conditions.append(f"puzzle_size IN ({sizes_str})")

    if filters.puzzle_difficulties:
        validated = [_validate_identifier(d) for d in filters.puzzle_difficulties]
        diffs_str = ", ".join(f"'{d}'" for d in validated)
        puzzle_conditions.append(f"puzzle_difficulty IN ({diffs_str})")

    puzzle_where = " AND ".join(puzzle_conditions)

    attempt_conditions = ["puzzle_id IN (SELECT id FROM puzzle)"]

    if filters.filter_user_id:
        validated_id = _validate_uuid(filters.filter_user_id)
        attempt_conditions.append(f"user_id = '{validated_id}'")

    if filters.filter_device_id:
        validated_id = _validate_uuid(filters.filter_device_id)
        attempt_conditions.append(f"device_id = '{validated_id}'")

    if filters.solved_filter == 'solved':
        attempt_conditions.append("is_solved = true")
    elif filters.solved_filter == 'unsolved':
        attempt_conditions.append("is_solved = false")

    if filters.user_type == 'authenticated':
        attempt_conditions.append("user_id IS NOT NULL")
    elif filters.user_type == 'anonymous':
        attempt_conditions.append("user_id IS NULL")

    if filters.date_start:
        attempt_conditions.append(f"created_at >= '{filters.date_start}'::date")

    if filters.date_end:
        attempt_conditions.append(f"created_at < ('{filters.date_end}'::date + interval '1 day')")

    attempt_where = " AND ".join(attempt_conditions)

    return f"""WITH puzzle AS (
  SELECT * FROM public.puzzle WHERE {puzzle_where}
),
freeplay_puzzle_attempt AS (
  SELECT * FROM public.freeplay_puzzle_attempt WHERE {attempt_where}
)
"""


################################################################################
# sql validation
_FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "COPY", "EXECUTE",
]


def validate_user_sql(sql: str) -> None:
    """validate user SQL is safe (SELECT only, no mutations)."""
    cleaned = sql.strip()
    if not cleaned:
        raise ValueError("SQL query cannot be empty")

    upper = cleaned.upper()

    if not upper.startswith("SELECT"):
        raise ValueError("Query must start with SELECT")

    for keyword in _FORBIDDEN_KEYWORDS:
        # Check for keyword as a standalone word
        if re.search(rf'\b{keyword}\b', upper):
            raise ValueError(f"Forbidden keyword: {keyword}")


################################################################################
# router
MAX_RESULT_ROWS = 500_000
STATEMENT_TIMEOUT_MS = 30_000

router = APIRouter(prefix="/api/data-export", tags=["Data Export"])


@router.post("/sql/preview")
async def preview_sql_query(
    request: SqlQueryRequest,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
):
    """
    Execute SQL query and return a preview (first 100 rows + total count).
    The sidebar filters define a CTE called 'base'. The user's SQL queries against it.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    try:
        validate_user_sql(request.sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base_cte = build_base_cte(request)

    try:
        from sqlalchemy import text as sa_text
        await db.execute(sa_text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_MS}'"))

        # count query
        count_sql = f"{base_cte} SELECT COUNT(*) FROM ({request.sql}) _count_subquery"
        count_result = await db.execute(sa_text(count_sql))
        total_rows = count_result.scalar()

        if total_rows > MAX_RESULT_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"Query returns {total_rows:,} rows, exceeding the limit of {MAX_RESULT_ROWS:,}. Add more filters or a LIMIT clause.",
            )

        # get preview rows
        has_limit = 'LIMIT' in request.sql.upper()
        preview_sql = f"{base_cte} {request.sql}" if has_limit else f"{base_cte} {request.sql} LIMIT 100"
        result = await db.execute(sa_text(preview_sql))
        columns = list(result.keys())
        rows = []
        for row in result.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Serialize non-JSON-safe types
                if isinstance(val, (uuid.UUID, datetime)):
                    val = str(val)
                elif isinstance(val, bytes):
                    val = val.hex()
                row_dict[col] = val
            rows.append(row_dict)

        return {
            "columns": columns,
            "rows": rows,
            "total_rows": total_rows,
            "preview_rows": len(rows),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")


@router.post("/sql/download")
async def download_sql_query(
    request: SqlQueryRequest,
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
):
    """
    Execute SQL query and return results as a Parquet file download.
    Uses caching to avoid re-executing identical queries.
    """
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    try:
        validate_user_sql(request.sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base_cte = build_base_cte(request)
    full_sql = base_cte + request.sql

    # check cache
    export_service = DataExportService(db)
    query_hash = DataExportService.hash_query(full_sql)

    cached = await export_service.get_cached_export(query_hash)
    if cached:
        return DataExportService.file_response(cached)

    try:
        from sqlalchemy import text as sa_text

        # set statement timeout and read-only transaction
        await db.execute(sa_text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_MS}'"))

        has_limit = 'LIMIT' in request.sql.upper()
        exec_sql = full_sql if has_limit else full_sql + f" LIMIT {MAX_RESULT_ROWS}"
        result = await db.execute(sa_text(exec_sql))
        columns = list(result.keys())
        rows = result.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Query returned no results")

        df = pd.DataFrame(rows, columns=columns)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json_mod.dumps(x) if isinstance(x, (dict, list)) else x)
            # Convert UUID columns to strings
            if df[col].apply(lambda x: isinstance(x, uuid.UUID)).any():
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, uuid.UUID) else x)

        export = await export_service.create_export(
            df=df,
            query_hash=query_hash,
            filters_json=request.model_dump(exclude={"sql"}),
            sql_query=request.sql,
            user_id=user.id,
            filename_prefix="sql_query",
        )
        return DataExportService.file_response(export)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")


@router.get("/schema")
async def get_database_schema(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
):
    """Return all public tables and their columns for SQL autocomplete."""
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    from sqlalchemy import text as sa_text

    result = await db.execute(sa_text(
        "SELECT table_name, column_name "
        "FROM information_schema.columns "
        "WHERE table_schema = 'public' "
        "ORDER BY table_name, ordinal_position"
    ))

    schema: dict[str, list[str]] = {}
    for table_name, column_name in result.fetchall():
        schema.setdefault(table_name, []).append(column_name)

    return schema


@router.get("/history")
async def list_exports(
    db: AsyncDatabase,
    user: User = Depends(fastapi_users.current_user()),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """list previously generated exports."""
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="admin access required")

    query = (
        select(GeneratedExport)
        .order_by(GeneratedExport.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    exports = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "filename": e.filename,
            "file_size": e.file_size,
            "row_count": e.row_count,
            "compression": e.compression,
            "sql_query": e.sql_query,
            "filters_json": e.filters_json,
        }
        for e in exports
    ]
