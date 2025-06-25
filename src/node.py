from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# ---- NODE SETUP ----
NODE_ID = os.environ.get("NODE_ID", "node1")
PEERS_RAW = os.environ.get("PEERS", "")
PEERS = [peer.split(":")[0] for peer in PEERS_RAW.split(",") if peer]

# ---- STATE ----
store = {}
vector_clock = {}
message_buffer = []

# ---- CLOCK INIT ----
def init_vector_clock():
    global vector_clock
    vector_clock[NODE_ID] = 0
    for peer in PEERS:
        vector_clock[peer] = 0

init_vector_clock()

# ---- CLOCK LOGIC ----
def increment_clock():
    vector_clock[NODE_ID] += 1

def update_clock(received_vc):
    for node, timestamp in received_vc.items():
        if node not in vector_clock:
            vector_clock[node] = 0
        vector_clock[node] = max(vector_clock[node], timestamp)

# ---- CAUSAL DELIVERY ----
def can_deliver(message_vc, sender):
    for node, ts in message_vc.items():
        local_ts = vector_clock.get(node, 0)
        if node == sender:
            if ts != local_ts + 1:
                return False
        else:
            if ts > local_ts:
                return False
    return True

def apply_write(msg):
    key = msg["key"]
    value = msg["value"]
    vc = msg["vector_clock"]
    store[key] = value
    update_clock(vc)

def process_buffer():
    delivered_any = True
    while delivered_any:
        delivered_any = False
        for msg in message_buffer[:]:
            if can_deliver(msg["vector_clock"], msg["sender"]):
                apply_write(msg)
                message_buffer.remove(msg)
                delivered_any = True

# ---- ROUTES ----

# Local write (e.g., from client)
@app.route("/write", methods=["POST"])
def write():
    data = request.json
    key = data["key"]
    value = data["value"]

    increment_clock()
    store[key] = value

    return jsonify({
        "status": "local_write_success",
        "vector_clock": vector_clock,
        "store": store
    })

# Handle replicated write from peer node
@app.route("/replicate", methods=["POST"])
def replicate():
    msg = request.json
    sender = msg["sender"]
    message_vc = msg["vector_clock"]

    if can_deliver(message_vc, sender):
        apply_write(msg)
        process_buffer()
        return jsonify({
            "status": "delivered",
            "vector_clock": vector_clock,
            "store": store
        })
    else:
        message_buffer.append(msg)
        return jsonify({"status": "buffered"})

# View current state (diagnostics)
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "node_id": NODE_ID,
        "vector_clock": vector_clock,
        "store": store,
        "buffered": message_buffer
    })

# ---- SERVER ----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
