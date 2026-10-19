import os
import uuid

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://127.0.0.1:5002")
INVENTORY_TIMEOUT_SECONDS = 2

ORDERS = {}


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/orders")
def create_order():
    body = request.get_json(silent=True) or {}
    item_id = body.get("item_id")
    quantity = body.get("quantity", 1)

    if not item_id or not isinstance(quantity, int) or quantity < 1:
        return jsonify({"error": "item_id is required and quantity must be a positive integer"}), 400

    try:
        resp = requests.get(
            f"{INVENTORY_URL}/inventory/{item_id}",
            params={"quantity": quantity},
            timeout=INVENTORY_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        app.logger.error("Inventory Service unreachable: %s", exc)
        return jsonify({
            "status": "failed",
            "error": "Inventory Service is unavailable. Please try again later.",
        }), 503

    if resp.status_code == 404:
        return jsonify({"status": "rejected", "error": f"item '{item_id}' does not exist"}), 404
    if resp.status_code != 200:
        return jsonify({"status": "failed", "error": "Inventory Service returned an error"}), 502

    availability = resp.json()["status"]
    if availability != "available":
        return jsonify({
            "status": "rejected",
            "item_id": item_id,
            "quantity": quantity,
            "reason": "item is unavailable",
        }), 409

    order_id = str(uuid.uuid4())
    order = {"order_id": order_id, "item_id": item_id, "quantity": quantity, "status": "created"}
    ORDERS[order_id] = order
    return jsonify(order), 201


@app.get("/orders/<order_id>")
def get_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify({"error": "order not found"}), 404
    return jsonify(order)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
