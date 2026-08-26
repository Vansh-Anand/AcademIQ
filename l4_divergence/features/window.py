from typing import List, Dict, Tuple, Optional
from common.events.schemas import SyscallEvent

class TrajectoryWindow:
    """
    Sliding window for buffering syscall events.
    Enforces deterministic ordering.
    """
    def __init__(self, agent_id: str, session_id: str, window_size: int = 256, stride: int = 64):
        self.agent_id = agent_id
        self.session_id = session_id
        self.window_size = window_size
        self.stride = stride
        
        self._buffer: List[SyscallEvent] = []
        self._window_counter = 0

    def append(self, event: SyscallEvent) -> bool:
        """Appends an event and returns True if the window is ready."""
        if event.agent_id != self.agent_id or event.session_id != self.session_id:
            return False
            
        self._buffer.append(event)
        
        # Sort to ensure deterministic ordering (primarily by timestamp, then event_id)
        self._buffer.sort(key=lambda x: (x.timestamp_ns, x.event_id or ""))
        
        return self.is_ready()
        
    def is_ready(self) -> bool:
        return len(self._buffer) >= self.window_size
        
    def build_window(self) -> List[SyscallEvent]:
        """Returns the current window of events."""
        if not self.is_ready():
            return []
        return list(self._buffer[:self.window_size])
        
    def advance(self) -> None:
        """Advances the window by stride."""
        if self.is_ready():
            self._buffer = self._buffer[self.stride:]
            self._window_counter += 1
            
    def reset(self) -> None:
        self._buffer = []
        self._window_counter = 0
