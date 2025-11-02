"""
End-to-end test for GraphFlow.

This script tests the complete workflow:
1. Load a graph definition
2. Compile it using the compiler
3. Upload to runtime
4. Execute the agent
5. Monitor execution and inspect memory
"""

import asyncio
import json
import time
from pathlib import Path
import httpx


# Configuration
RUNTIME_URL = "http://localhost:8000/api/v1"
EXAMPLE_GRAPH = "examples/simple_agent.json"


async def main():
    print("=" * 70)
    print("GraphFlow End-to-End Test")
    print("=" * 70)
    print()

    # Step 1: Load graph definition
    print("1. Loading graph definition...")
    graph_path = Path(EXAMPLE_GRAPH)
    with open(graph_path) as f:
        graph_data = json.load(f)
    print(f"✓ Loaded: {graph_data['metadata']['name']}")
    print()

    # Step 2: Check runtime is available
    print("2. Checking runtime server...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{RUNTIME_URL}/health", timeout=5.0)
            response.raise_for_status()
            health = response.json()
            print(f"✓ Runtime healthy: {health}")
        except Exception as e:
            print(f"✗ Runtime not available: {e}")
            print("\nPlease start the runtime server:")
            print("  graphflow-runtime")
            return
    print()

    # Step 3: Create agent
    print("3. Creating agent in runtime...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RUNTIME_URL}/agents",
            json={
                "name": graph_data['metadata']['name'],
                "description": graph_data['metadata']['description'],
                "framework": "pydantic_ai",
                "graph_definition": graph_data
            },
            timeout=30.0
        )
        response.raise_for_status()
        agent = response.json()
        agent_id = agent['id']
    print(f"✓ Agent created: {agent_id}")
    print(f"  Name: {agent['name']}")
    print(f"  Framework: {agent['framework']}")
    print()

    # Step 4: Start agent run
    print("4. Starting agent run...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RUNTIME_URL}/agents/{agent_id}/runs",
            json={
                "inputs": {
                    "user_question": "What is the capital of France?"
                }
            },
            timeout=30.0
        )
        response.raise_for_status()
        run = response.json()
        run_id = run['id']
    print(f"✓ Run started: {run_id}")
    print(f"  Status: {run['status']}")
    print()

    # Step 5: Monitor run status
    print("5. Monitoring run status...")
    max_wait = 30  # seconds
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        while time.time() - start_time < max_wait:
            response = await client.get(
                f"{RUNTIME_URL}/agents/{agent_id}/runs/{run_id}",
                timeout=10.0
            )
            response.raise_for_status()
            run = response.json()

            print(f"  Status: {run['status']}", end="\r")

            if run['status'] in ['completed', 'failed', 'stopped']:
                break

            await asyncio.sleep(0.5)

    print()  # New line after status updates

    if run['status'] == 'completed':
        print(f"✓ Run completed successfully")
        print(f"  Duration: {(time.time() - start_time):.2f}s")

        if run.get('outputs'):
            print(f"\n  Outputs:")
            for key, value in run['outputs'].items():
                print(f"    {key}: {value}")
    elif run['status'] == 'failed':
        print(f"✗ Run failed: {run.get('error')}")
    else:
        print(f"⚠ Run status: {run['status']}")
    print()

    # Step 6: Inspect memory (if still available)
    print("6. Inspecting memory...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{RUNTIME_URL}/agents/{agent_id}/runs/{run_id}/memory",
                timeout=10.0
            )
            if response.status_code == 200:
                memory = response.json()
                print(f"✓ Memory state retrieved")
                print(f"  Inputs: {list(memory.get('inputs', {}).keys())}")
                print(f"  Outputs: {list(memory.get('outputs', {}).keys())}")
                print(f"  Intermediate: {list(memory.get('intermediate', {}).keys())}")
            else:
                print(f"  Memory not available (run may have completed)")
        except Exception as e:
            print(f"  Memory not available: {e}")
    print()

    # Step 7: Cleanup (optional)
    print("7. Cleanup...")
    async with httpx.AsyncClient() as client:
        # Delete run
        response = await client.delete(
            f"{RUNTIME_URL}/agents/{agent_id}/runs/{run_id}",
            timeout=10.0
        )
        if response.status_code == 204:
            print(f"✓ Run deleted")

        # Delete agent
        response = await client.delete(
            f"{RUNTIME_URL}/agents/{agent_id}",
            timeout=10.0
        )
        if response.status_code == 204:
            print(f"✓ Agent deleted")
    print()

    print("=" * 70)
    print("End-to-End Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
