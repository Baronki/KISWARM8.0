import time
import subprocess
import json
import statistics

MODELS = ["kiswarm-orchestrator:latest", "lfm2:latest"]

TEST_CASES = [
    {
        "name": "Industrial Safety (CIEC Logic)",
        "prompt": "SCENARIO: Reactor pressure is at 7.2 bar and rising at 0.2 bar/sec. The OVERPRESSURE_BLOCK hard limit is 8.0 bar. 1) Calculate seconds until breach. 2) Propose a mitigation action according to KISWARM Module 14 Rule Engine. 3) Output response in valid JSON.",
        "category": "industrial"
    },
    {
        "name": "Task Orchestration (Coordination)",
        "prompt": "TASK: 'Detect anomalous behavior in the Solar Chase energy routing'. 1) Route this task to the correct KISWARM agents. 2) List exactly which modules (1-57) must be involved. 3) Provide a step-by-step execution plan.",
        "category": "orchestration"
    },
    {
        "name": "Complex Reasoning (Stability)",
        "prompt": "EXPLAIN: The process of a SHA-256 Merkle Tree inclusion proof for a knowledge block in the KISWARM CryptoLedger. Provide a logical sequence of 5 steps and ensure the technical terminology is correct.",
        "category": "stability"
    }
]

def run_ollama(model, prompt):
    start_time = time.time()
    try:
        process = subprocess.Popen(
            ["ollama", "run", model, prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        end_time = time.time()
        
        duration = end_time - start_time
        return stdout.strip(), duration
    except Exception as e:
        return str(e), 0

def benchmark():
    results = {}
    
    print("\n🚀 KISWARM Benchmarking: Qwen-Orchestrator vs Liquid LFM2")
    print("=" * 60)
    
    for model in MODELS:
        print(f"\n[MODEL] {model}")
        results[model] = []
        
        for test in TEST_CASES:
            print(f"  [TEST] {test['name']}...", end="", flush=True)
            output, duration = run_ollama(model, test['prompt'])
            
            has_json = "{" in output and "}" in output
            word_count = len(output.split())
            tps = word_count / duration if duration > 0 else 0
            
            results[model].append({
                "test": test['name'],
                "duration": duration,
                "tps_approx": tps,
                "has_json": has_json
            })
            print(f" Done ({duration:.2f}s, ~{tps:.1f} tokens/s)")

    print("\n" + "=" * 60)
    print("📊 FINAL STABILITY REPORT")
    print("=" * 60)
    
    for model in MODELS:
        speeds = [r['tps_approx'] for r in results[model]]
        avg_speed = statistics.mean(speeds) if speeds else 0
        json_stability = sum([1 for r in results[model] if r['has_json']]) / len(TEST_CASES) * 100
        
        print(f"\nModel: {model}")
        print(f"  Average Speed: {avg_speed:.2f} tokens/sec")
        print(f"  Format Stability: {json_stability:.0f}% JSON Compliance")
        
        for r in results[model]:
            success = "✅" if r['has_json'] or "Reasoning" in r['test'] else "❌"
            print(f"  - {r['test']}: {r['duration']:.2f}s | Success: {success}")

if __name__ == "__main__":
    benchmark()
