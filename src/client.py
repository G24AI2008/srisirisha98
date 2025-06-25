import requests
import time

# URLs
NODE1 = "http://localhost:5001"
NODE2 = "http://localhost:5002"
NODE3 = "http://localhost:5003"

def print_state(label):
    print(f"\n📦 {label}")
    for i, node in enumerate([NODE1, NODE2, NODE3], start=1):
        r = requests.get(f"{node}/")
        print(f"Node{i}: {r.json()}")

def main():
    print_state("Initial state")

    # Step 1: Local write to node1 (x = 'A')
    print("\n✏️ Write x='A' to Node1")
    res = requests.post(f"{NODE1}/write", json={"key": "x", "value": "A"})
    vc = res.json()["vector_clock"]
    print("Node1 vector clock after write:", vc)

    # Step 2: Send replicated write to Node3 BEFORE Node2 (simulate out-of-order)
    msg = {
        "key": "x",
        "value": "A",
        "sender": "node1",
        "vector_clock": vc
    }

    print("\n🚚 Replicating to Node3 (should be buffered)")
    res3 = requests.post(f"{NODE3}/replicate", json=msg)
    print("Node3 replicate response:", res3.json())

    print("\n🚚 Replicating to Node2 (should be delivered)")
    res2 = requests.post(f"{NODE2}/replicate", json=msg)
    print("Node2 replicate response:", res2.json())

    # Wait for buffers to process
    time.sleep(1)

    print_state("After Replication")

if __name__ == "__main__":
    main()
