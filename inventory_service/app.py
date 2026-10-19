from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY = {
    "apple": 10,
    "banana": 0,
    "laptop": 3,
    "headphones": 5,
}


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/inventory/<item_id>")
def check_availability(item_id):
    quantity = request.args.get("quantity", default=1, type=int)
    if quantity is None or quantity < 1:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    if item_id not in INVENTORY:
        return jsonify({"error": f"item '{item_id}' not found"}), 404

    in_stock = INVENTORY[item_id]
    return jsonify({
        "item_id": item_id,
        "requested": quantity,
        "in_stock": in_stock,
        "status": "available" if in_stock >= quantity else "unavailable",
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
