"""
Tests for miscellaneous API endpoints (demand, backlog, spending).
"""
import pytest


class TestDemandEndpoints:
    """Test suite for demand forecast endpoints."""

    def test_get_demand_forecasts(self, client):
        """Test getting demand forecasts."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if data exists
        if len(data) > 0:
            forecast = data[0]
            assert "id" in forecast
            assert "item_sku" in forecast
            assert "item_name" in forecast
            assert "current_demand" in forecast
            assert "forecasted_demand" in forecast
            assert "trend" in forecast
            assert "period" in forecast

    def test_demand_forecast_trends(self, client):
        """Test that demand forecasts have valid trend values."""
        response = client.get("/api/demand")
        data = response.json()

        valid_trends = ["increasing", "stable", "decreasing"]

        for forecast in data:
            assert forecast["trend"].lower() in valid_trends

    def test_demand_forecast_values(self, client):
        """Test that demand forecast values are non-negative."""
        response = client.get("/api/demand")
        data = response.json()

        for forecast in data:
            assert forecast["current_demand"] >= 0
            assert forecast["forecasted_demand"] >= 0

    def test_stable_demand_items_have_small_changes(self, client):
        """Test that items with 'stable' trend have less than 2% change."""
        response = client.get("/api/demand")
        data = response.json()

        stable_items = [item for item in data if item["trend"].lower() == "stable"]

        # Should have at least 5 stable items
        assert len(stable_items) >= 5, f"Expected at least 5 stable items, found {len(stable_items)}"

        for item in stable_items:
            current = item["current_demand"]
            forecasted = item["forecasted_demand"]

            # Calculate percentage change
            if current > 0:
                percent_change = abs((forecasted - current) / current) * 100
                assert percent_change < 2.0, \
                    f"Item {item['item_name']} has {percent_change:.2f}% change, expected < 2%"

    def test_demand_forecast_covers_inventory_skus(self, client):
        """Test that demand forecasts reference real inventory SKUs."""
        forecasts = client.get("/api/demand").json()
        inventory_skus = {item["sku"] for item in client.get("/api/inventory").json()}

        skus = [item["item_sku"] for item in forecasts]
        assert "PSU-501" in skus, "Missing 5V 10A Switching Power Supply"
        assert "HMD-202" in skus, "Missing Humidity Sensor Module"

        # Every forecast must map onto an inventory item so restocking can price it
        for item in forecasts:
            assert item["item_sku"] in inventory_skus, \
                f"Forecast SKU {item['item_sku']} does not exist in inventory"

        # Verify the two reference items are marked as stable
        for item in forecasts:
            if item["item_sku"] in ["PSU-501", "HMD-202"]:
                assert item["trend"].lower() == "stable", \
                    f"Item {item['item_name']} should have stable trend"


class TestBacklogEndpoints:
    """Test suite for backlog endpoints."""

    def test_get_backlog(self, client):
        """Test getting backlog items."""
        response = client.get("/api/backlog")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if data exists
        if len(data) > 0:
            backlog_item = data[0]
            assert "id" in backlog_item
            assert "order_id" in backlog_item
            assert "item_sku" in backlog_item
            assert "item_name" in backlog_item
            assert "quantity_needed" in backlog_item
            assert "quantity_available" in backlog_item
            assert "days_delayed" in backlog_item
            assert "priority" in backlog_item

    def test_backlog_priority_values(self, client):
        """Test that backlog items have valid priority values."""
        response = client.get("/api/backlog")
        data = response.json()

        valid_priorities = ["high", "medium", "low"]

        for item in data:
            assert item["priority"].lower() in valid_priorities

    def test_backlog_quantity_logic(self, client):
        """Test that backlog quantities are non-negative."""
        response = client.get("/api/backlog")
        data = response.json()

        for item in data:
            # Quantities should be non-negative
            assert item["quantity_needed"] >= 0
            assert item["quantity_available"] >= 0

    def test_backlog_days_delayed(self, client):
        """Test that days delayed is non-negative."""
        response = client.get("/api/backlog")
        data = response.json()

        for item in data:
            assert item["days_delayed"] >= 0


class TestSpendingEndpoints:
    """Test suite for spending-related endpoints."""

    def test_get_spending_summary(self, client):
        """Test getting spending summary."""
        response = client.get("/api/spending/summary")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_get_monthly_spending(self, client):
        """Test getting monthly spending data."""
        response = client.get("/api/spending/monthly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if data exists
        if len(data) > 0:
            month_data = data[0]
            assert "month" in month_data or "period" in month_data

    def test_monthly_spending_has_all_cost_categories(self, client):
        """Test that monthly spending includes all cost categories."""
        response = client.get("/api/spending/monthly")
        data = response.json()

        required_fields = ["procurement", "operational", "labor", "overhead"]

        for month_data in data:
            for field in required_fields:
                assert field in month_data, f"Missing {field} in monthly spending"
                assert isinstance(month_data[field], (int, float))
                assert month_data[field] >= 0

    def test_monthly_spending_has_variety(self, client):
        """Test that monthly spending data has variety (not all the same)."""
        response = client.get("/api/spending/monthly")
        data = response.json()

        # Collect all procurement values
        procurement_values = [month["procurement"] for month in data]

        # Should have at least 3 different values (variety)
        unique_values = set(procurement_values)
        assert len(unique_values) >= 3, \
            "Monthly spending should have variety, not all the same values"

        # Same for other categories
        operational_values = set(month["operational"] for month in data)
        assert len(operational_values) >= 3, \
            "Operational costs should have variety across months"

    def test_get_category_spending(self, client):
        """Test getting spending by category."""
        response = client.get("/api/spending/categories")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if data exists
        if len(data) > 0:
            category_data = data[0]
            assert "category" in category_data or "name" in category_data

    def test_get_recent_transactions(self, client):
        """Test getting recent transactions."""
        response = client.get("/api/spending/transactions")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Check structure if data exists
        if len(data) > 0:
            transaction = data[0]
            # Transactions should have some identifying fields
            assert isinstance(transaction, dict)


class TestRootEndpoint:
    """Test suite for root endpoint."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data or "version" in data

    def test_root_endpoint_structure(self, client):
        """Test root endpoint has expected structure."""
        response = client.get("/")
        data = response.json()

        # Should have message and version
        assert "message" in data
        assert "version" in data
        assert isinstance(data["message"], str)
        assert isinstance(data["version"], str)


class TestTasksEndpoints:
    """Test suite for the header tasks endpoint."""

    def test_get_tasks(self, client):
        """GET /api/tasks returns a list of tasks in the shape the TasksModal expects."""
        response = client.get("/api/tasks")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for task in data:
            # camelCase dueDate is intentional: the Vue client reads task.dueDate directly
            assert set(task.keys()) == {"id", "title", "priority", "dueDate", "status"}
            assert task["priority"] in ["high", "medium", "low"]
            assert task["status"] in ["pending", "completed"]

    def test_tasks_have_unique_ids(self, client):
        """Task ids must be unique so v-for keys and delete-by-id behave correctly."""
        data = client.get("/api/tasks").json()
        ids = [task["id"] for task in data]
        assert len(ids) == len(set(ids))


class TestReportsEndpoints:
    """Test suite for the reports endpoints and their filter support."""

    def test_quarterly_reports_unfiltered(self, client):
        """GET /api/reports/quarterly returns sorted quarters with computed metrics."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert [q["quarter"] for q in data] == sorted(q["quarter"] for q in data)
        for q in data:
            assert {"quarter", "total_orders", "total_revenue", "avg_order_value", "fulfillment_rate"} <= set(q)
            assert 0 <= q["fulfillment_rate"] <= 100

    def test_quarterly_reports_month_filter(self, client):
        """A single-month filter must collapse the result to that month's quarter only."""
        data = client.get("/api/reports/quarterly?month=2025-02").json()
        assert [q["quarter"] for q in data] == ["Q1-2025"]
        # Order count must match what /api/orders returns for the same filter
        orders = client.get("/api/orders?month=2025-02").json()
        assert data[0]["total_orders"] == len(orders)

    def test_quarterly_reports_warehouse_filter(self, client):
        """Warehouse filter must reduce totals relative to the unfiltered report."""
        all_q = client.get("/api/reports/quarterly").json()
        sf_q = client.get("/api/reports/quarterly?warehouse=San Francisco").json()
        assert sum(q["total_orders"] for q in sf_q) < sum(q["total_orders"] for q in all_q)
        assert sum(q["total_orders"] for q in sf_q) == len(client.get("/api/orders?warehouse=San Francisco").json())

    def test_monthly_trends_filters(self, client):
        """Monthly trends honor month and status filters like /api/orders."""
        unfiltered = client.get("/api/reports/monthly-trends").json()
        assert len(unfiltered) == 12
        assert [m["month"] for m in unfiltered] == sorted(m["month"] for m in unfiltered)

        one_month = client.get("/api/reports/monthly-trends?month=2025-03").json()
        assert [m["month"] for m in one_month] == ["2025-03"]

        delivered = client.get("/api/reports/monthly-trends?status=Delivered").json()
        delivered_orders = client.get("/api/orders?status=Delivered").json()
        assert sum(m["order_count"] for m in delivered) == len(delivered_orders)

    def test_reports_ignore_all_sentinel(self, client):
        """Passing 'all' must behave exactly like omitting the filter."""
        plain = client.get("/api/reports/quarterly").json()
        with_all = client.get("/api/reports/quarterly?warehouse=all&category=all&status=all&month=all").json()
        assert plain == with_all
