import time
import numpy as np
import base64
from common.events.schemas import ShellCommandEvent
from l2_sdn.interceptor import DevelopmentShellInterceptor

def generate_obfuscated_commands():
    return [
        "cat /tmp/safe.txt",
        "rm -rf /tmp",
        f"{base64.b64encode(b'rm').decode()} /tmp",
        "\\x72\\x6d /tmp",
        "\\162\\155 /tmp",
        "cat /tmp/../etc/passwd",
        "cat \"/et\"c/passwd",
        "cat /etc/./././passwd",
        "ls | cat",
        "cat $(echo /etc/passwd)"
    ]

def run_benchmark(iterations: int = 100):
    interceptor = DevelopmentShellInterceptor()
    commands = generate_obfuscated_commands()
    
    latencies_ns = []
    blocked_count = 0
    total_dangerous = 0
    
    print(f"Running L2 SDN latency benchmark with {iterations} iterations...")
    
    for cmd in commands:
        is_dangerous = "rm" in cmd or "passwd" in cmd or "\\" in cmd or "base64" in cmd
        if is_dangerous:
            total_dangerous += iterations
            
        for _ in range(iterations):
            event = ShellCommandEvent(
                event_id="bench",
                timestamp_ns=time.time_ns(),
                trace_id="bench-trace",
                layer="L2",
                raw_command=cmd
            )
            
            start = time.time_ns()
            decision, _ = interceptor.intercept(event)
            end = time.time_ns()
            
            latencies_ns.append(end - start)
            
            if is_dangerous and decision == "BLOCK":
                blocked_count += 1
                
    latencies_ms = np.array(latencies_ns) / 1_000_000
    
    mean = np.mean(latencies_ms)
    median = np.median(latencies_ms)
    p95 = np.percentile(latencies_ms, 95)
    p99 = np.percentile(latencies_ms, 99)
    
    decode_rate = (blocked_count / total_dangerous) * 100 if total_dangerous > 0 else 100
    
    print("\n======================================")
    print(" L2 SDN LATENCY & COVERAGE BENCHMARK  ")
    print("======================================")
    print(f"Mean Latency   : {mean:.3f} ms")
    print(f"Median Latency : {median:.3f} ms")
    print(f"P95 Latency    : {p95:.3f} ms")
    print(f"P99 Latency    : {p99:.3f} ms")
    print("--------------------------------------")
    print(f"Obfuscation Decode Rate : {decode_rate:.2f}%")
    print(f"(Target >98%)")
    print("======================================")

if __name__ == "__main__":
    run_benchmark()
