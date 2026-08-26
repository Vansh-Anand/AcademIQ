import time
from common.events.schemas import TelemetryHealthEvent

class TelemetryHealthMonitor:
    """
    Monitors the BPF ring buffer throughput and latencies.
    Emits TelemetryHealthEvent periodically.
    Crucial for detecting loss of telemetry (which forces fail-closed).
    """
    def __init__(self, check_interval_ms: int = 1000):
        self.check_interval_ms = check_interval_ms
        self.events_received = 0
        self.events_dropped = 0
        self.ringbuf_overflows = 0
        self.decode_errors = 0
        self.total_latency_ms = 0.0
        
        self.last_report_time = time.time_ns()
        self.last_event_time = 0
        
    def record_event(self, processing_latency_ms: float):
        self.events_received += 1
        self.total_latency_ms += processing_latency_ms
        self.last_event_time = time.time_ns()
        
    def record_drop(self):
        self.events_dropped += 1
        
    def record_overflow(self):
        self.ringbuf_overflows += 1
        
    def record_decode_error(self):
        self.decode_errors += 1
        
    def should_report(self) -> bool:
        now = time.time_ns()
        return (now - self.last_report_time) / 1_000_000 >= self.check_interval_ms
        
    def generate_report(self) -> TelemetryHealthEvent:
        avg_latency = 0.0
        if self.events_received > 0:
            avg_latency = self.total_latency_ms / self.events_received
            
        import uuid
        event = TelemetryHealthEvent(
            event_id=f"evt-{uuid.uuid4()}",
            timestamp_ns=time.time_ns(),
            layer="L3",
            trace_id="health-monitor",
            events_received=self.events_received,
            events_dropped=self.events_dropped,
            ringbuf_overflow=self.ringbuf_overflows,
            decode_errors=self.decode_errors,
            collector_latency_ms=avg_latency,
            last_event_timestamp_ns=self.last_event_time
        )
        
        # Reset counters for next window
        self.events_received = 0
        self.events_dropped = 0
        self.ringbuf_overflows = 0
        self.decode_errors = 0
        self.total_latency_ms = 0.0
        self.last_report_time = time.time_ns()
        
        return event
