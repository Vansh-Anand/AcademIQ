from typing import Optional
from pydantic import BaseModel, Field
import time

class PathIdentity(BaseModel):
    path: str
    resolved_path: str
    device_id: Optional[int] = None
    inode_id: Optional[int] = None
    file_type: str = "UNKNOWN"
    mode: Optional[int] = None
    uid: Optional[int] = None
    gid: Optional[int] = None
    size: Optional[int] = None
    mtime_ns: Optional[int] = None
    symlink_chain: list[str] = []
    resolution_timestamp_ns: int = Field(default_factory=time.time_ns)
