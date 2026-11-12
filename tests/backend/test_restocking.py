"""
Tests for restocking recommendation and order endpoints.
"""
import json
from datetime import datetime

import pytest

import mock_data


@pytest.fixture
def isolated_restocking(monkeypatch, tmp_path):
    """Redirect JSON writes to tmp_path and start each test with an empty order list."""
    target = tmp_path / "restocking_orders.json"
    monkeypatch.setattr(mock_data, "RESTOCKING_ORDERS_FILE", str(target))
    saved = list(mock_data.restocking_orders)
    # Mutate in place: main.py imported the same list object
    mock_data.restocking_orders.clear()
    yield target
    mock_data.restocking_orders[:] = saved


RECOMMENDATION_KEYS = {
    "sku", "name", "category", "warehouse", "quantity_on_hand", "on_order",
    "reorder_point", "forecasted_demand", "trend", "recommended_quantity",
    "quantity", "unit_cost", "line_total", "lead_time_days", "urgency_score",
    "priority", "is_partial",
}


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_unlimited_budget_returns_full_need(self, client, isolated_restocking):
        """Test that omitting budget funds every shortfall."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        for key in ["budget", "full_need_total", "total_cost", "remaining_budget",
                    "items", "unfunded", "sufficient_count"]:
            assert key in data

        assert data["budget"] is None
        assert data["unfunded"] == []
        assert data["total_cost"] == data["full_need_total"]
        assert len(data["items"]) > 0
        assert data["sufficient_count"] >= 1

        for item in data["items"]:
            assert RECOMMENDATION_KEYS <= set(item.keys())
            assert item["quantity"] == item["recommended_quantity"]
            assert item["is_partial"] is False
            assert item["priority"] in ["high", "medium", "low"]

    def test_zero_budget_funds_nothing(self, client, isolated_restocking):
        """Test that a zero budget leaves every item unfunded."""
        data = client.get("/api/restocking/recommendations?budget=0").json()

        assert data["items"] == []
        assert data["total_cost"] == 0
        assert len(data["unfunded"]) > 0
        for item in data["unfunded"]:
            assert item["quantity"] == 0

    def test_budget_is_respected(self, client, isolated_restocking):
        """Test that funded lines never exceed the budget."""
        budget = 50000
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()

        assert data["total_cost"] <= budget
        assert abs(data["total_cost"] + data["remaining_budget"] - budget) < 0.01
        assert len(data["items"]) > 0
        assert len(data["unfunded"]) > 0, "Expected some items to be unaffordable at this budget"

        for item in data["items"]:
            assert 0 < item["quantity"] <= item["recommended_quantity"]
            assert item["is_partial"] == (item["quantity"] < item["recommended_quantity"])
            assert abs(item["line_total"] - round(item["quantity"] * item["unit_cost"], 2)) < 0.01

    def test_items_sorted_by_urgency(self, client, isolated_restocking):
        """Test that the most urgent items are listed first."""
        data = client.get("/api/restocking/recommendations").json()
        scores = [item["urgency_score"] for item in data["items"]]
        assert scores == sorted(scores, reverse=True)

    def test_warehouse_filter_restricts_items(self, client, isolated_restocking):
        """Test that the warehouse filter limits recommendations to that warehouse."""
        data = client.get("/api/restocking/recommendations?warehouse=Tokyo").json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["warehouse"] == "Tokyo"

    def test_negative_budget_rejected(self, client, isolated_restocking):
        """Test that a negative budget fails validation."""
        response = client.get("/api/restocking/recommendations?budget=-1")
        assert response.status_code == 422

    def test_submitted_orders_count_as_on_order(self, client, isolated_restocking):
        """Test that ordering an item's full need removes it from recommendations."""
        before = client.get("/api/restocking/recommendations").json()["items"]
        top = before[0]

        response = client.post("/api/restocking/orders", json={
            "budget": top["line_total"] + 1,
            "items": [{"sku": top["sku"], "quantity": top["recommended_quantity"]}],
        })
        assert response.status_code == 201

        after = client.get("/api/restocking/recommendations").json()["items"]
        assert top["sku"] not in [item["sku"] for item in after]


class TestRestockingOrders:
    """Test suite for /api/restocking/orders."""

    def _valid_payload(self):
        return {
            "budget": 50000,
            "items": [
                {"sku": "TMP-201", "quantity": 10},   # Sensors, 7 days
                {"sku": "SRV-302", "quantity": 5},    # Actuators, 21 days
            ],
        }

    def test_create_order(self, client, isolated_restocking):
        """Test that a valid order is created and persisted."""
        response = client.post("/api/restocking/orders", json=self._valid_payload())
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert order["budget"] == 50000
        assert len(order["items"]) == 2
        assert order["total_value"] == round(10 * 89.5 + 5 * 725.0, 2)

        # Lead time is the slowest line; delivery is created_at + lead time
        assert order["lead_time_days"] == 21
        created = datetime.fromisoformat(order["created_at"])
        delivery = datetime.fromisoformat(order["expected_delivery"])
        assert (delivery - created).days == 21

        # Persisted to the (isolated) JSON file
        saved = json.loads(isolated_restocking.read_text())
        assert len(saved) == 1
        assert saved[0]["order_number"] == order["order_number"]

    def test_list_orders_newest_first(self, client, isolated_restocking):
        """Test that submitted orders are listed newest first."""
        first = client.post("/api/restocking/orders", json=self._valid_payload()).json()
        second = client.post("/api/restocking/orders", json=self._valid_payload()).json()

        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert [o["order_number"] for o in data] == [second["order_number"], first["order_number"]]

    def test_unknown_sku_rejected(self, client, isolated_restocking):
        """Test that an unknown SKU returns 404."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000, "items": [{"sku": "NOPE-000", "quantity": 1}],
        })
        assert response.status_code == 404

    def test_empty_items_rejected(self, client, isolated_restocking):
        """Test that an order without items returns 400."""
        response = client.post("/api/restocking/orders", json={"budget": 1000, "items": []})
        assert response.status_code == 400

    def test_zero_quantity_rejected(self, client, isolated_restocking):
        """Test that a non-positive quantity returns 400."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000, "items": [{"sku": "TMP-201", "quantity": 0}],
        })
        assert response.status_code == 400

    def test_duplicate_sku_rejected(self, client, isolated_restocking):
        """Test that the same SKU twice in one order returns 400."""
        response = client.post("/api/restocking/orders", json={
            "budget": 10000,
            "items": [{"sku": "TMP-201", "quantity": 1}, {"sku": "TMP-201", "quantity": 2}],
        })
        assert response.status_code == 400

    def test_total_over_budget_rejected(self, client, isolated_restocking):
        """Test that an order costing more than its budget returns 400."""
        response = client.post("/api/restocking/orders", json={
            "budget": 10, "items": [{"sku": "SRV-302", "quantity": 1}],
        })
        assert response.status_code == 400
        assert len(client.get("/api/restocking/orders").json()) == 0
