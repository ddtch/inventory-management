from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import mock_data
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restocking_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str
    # Default keeps older fixtures/JSON without the field valid
    lead_time_days: int = 14

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

# Restocking models
class RestockingRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    on_order: int               # units already in submitted restocking orders
    reorder_point: int
    forecasted_demand: int
    trend: str
    recommended_quantity: int   # full quantity needed, ignoring budget
    quantity: int               # quantity actually funded by the budget
    unit_cost: float
    line_total: float
    lead_time_days: int
    urgency_score: float
    priority: str               # high | medium | low
    is_partial: bool

class RestockingRecommendationsResponse(BaseModel):
    budget: Optional[float] = None
    full_need_total: float
    total_cost: float
    remaining_budget: Optional[float] = None
    items: List[RestockingRecommendation]
    unfunded: List[RestockingRecommendation]
    sufficient_count: int

class RestockingOrderItemRequest(BaseModel):
    sku: str
    quantity: int

class CreateRestockingOrderRequest(BaseModel):
    budget: float
    items: List[RestockingOrderItemRequest]

class RestockingOrderItem(BaseModel):
    sku: str
    name: str
    category: str
    warehouse: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    status: str
    created_at: str
    budget: float
    total_value: float
    lead_time_days: int
    expected_delivery: str
    items: List[RestockingOrderItem]

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

# ---------------------------------------------------------------------------
# Restocking
# ---------------------------------------------------------------------------

# Used as a tie-breaker: when two items are equally urgent, growing demand
# should be restocked before flat or shrinking demand.
TREND_RANK = {'increasing': 0, 'stable': 1, 'decreasing': 2}

def _priority_for(urgency_score: float) -> str:
    # >= 1.0 means stock is already below the safety buffer for the period
    if urgency_score >= 1.0:
        return 'high'
    if urgency_score >= 0.5:
        return 'medium'
    return 'low'

def build_recommendations(budget: Optional[float], warehouse: Optional[str] = None,
                          category: Optional[str] = None) -> dict:
    """Join demand forecasts with inventory and greedily fund the most urgent items."""
    inventory_by_sku = {item['sku']: item for item in apply_filters(inventory_items, warehouse, category)}

    # Units already ordered count as available stock, otherwise the same item
    # would be recommended again right after the user places an order.
    on_order: dict = {}
    for order in restocking_orders:
        for line in order['items']:
            on_order[line['sku']] = on_order.get(line['sku'], 0) + line['quantity']

    candidates = []
    sufficient_count = 0
    for forecast in demand_forecasts:
        item = inventory_by_sku.get(forecast['item_sku'])
        # Forecasts without an inventory row have no cost or stock level, so
        # there is nothing to recommend against; skip them silently.
        if item is None:
            continue

        # Target stock = forecasted 30-day demand + reorder point (safety buffer).
        available = item['quantity_on_hand'] + on_order.get(item['sku'], 0)
        need = max(0, forecast['forecasted_demand'] + item['reorder_point'] - available)
        if need == 0:
            sufficient_count += 1
            continue

        # Share of forecasted demand that current stock cannot cover.
        # Values above 1.0 mean stock is below the safety buffer itself.
        urgency = round(need / forecast['forecasted_demand'], 3) if forecast['forecasted_demand'] else 1.0
        candidates.append({
            'sku': item['sku'],
            'name': item['name'],
            'category': item['category'],
            'warehouse': item['warehouse'],
            'quantity_on_hand': item['quantity_on_hand'],
            'on_order': on_order.get(item['sku'], 0),
            'reorder_point': item['reorder_point'],
            'forecasted_demand': forecast['forecasted_demand'],
            'trend': forecast['trend'],
            'recommended_quantity': need,
            'unit_cost': item['unit_cost'],
            'lead_time_days': item.get('lead_time_days', 14),
            'urgency_score': urgency,
            'priority': _priority_for(urgency),
        })

    candidates.sort(key=lambda c: (-c['urgency_score'], TREND_RANK.get(c['trend'], 1), c['sku']))

    full_need_total = round(sum(c['recommended_quantity'] * c['unit_cost'] for c in candidates), 2)

    funded, unfunded = [], []
    remaining = budget
    for c in candidates:
        if budget is None:
            qty = c['recommended_quantity']
        else:
            # Greedy fill: take as much of this line as the remaining budget
            # allows, so the most urgent item gets at least a partial order.
            qty = min(c['recommended_quantity'], int(remaining // c['unit_cost']))
        line_total = round(qty * c['unit_cost'], 2)
        entry = {**c, 'quantity': qty, 'line_total': line_total,
                 'is_partial': 0 < qty < c['recommended_quantity']}
        if qty > 0:
            funded.append(entry)
            if remaining is not None:
                remaining = round(remaining - line_total, 2)
        else:
            unfunded.append(entry)

    return {
        'budget': budget,
        'full_need_total': full_need_total,
        'total_cost': round(sum(e['line_total'] for e in funded), 2),
        'remaining_budget': remaining,
        'items': funded,
        'unfunded': unfunded,
        'sufficient_count': sufficient_count,
    }

@app.get("/api/restocking/recommendations", response_model=RestockingRecommendationsResponse)
def get_restocking_recommendations(
    budget: Optional[float] = Query(None, ge=0),
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Recommend items to restock within a budget. Omit budget for the unconstrained need."""
    return build_recommendations(budget, warehouse, category)

@app.get("/api/restocking/orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """List submitted restocking orders, newest first."""
    # Two orders placed within the same second share created_at, so fall back
    # to the numeric id to keep "newest first" deterministic.
    return sorted(restocking_orders, key=lambda o: (o['created_at'], int(o['id'])), reverse=True)

@app.post("/api/restocking/orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Submit a restocking order and persist it to disk."""
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    skus = [line.sku for line in request.items]
    if len(set(skus)) != len(skus):
        raise HTTPException(status_code=400, detail="Duplicate SKU in order")

    inventory_by_sku = {item['sku']: item for item in inventory_items}
    line_items = []
    for line in request.items:
        if line.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Quantity for {line.sku} must be positive")
        item = inventory_by_sku.get(line.sku)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Item {line.sku} not found")
        line_items.append({
            'sku': item['sku'],
            'name': item['name'],
            'category': item['category'],
            'warehouse': item['warehouse'],
            'quantity': line.quantity,
            'unit_cost': item['unit_cost'],
            'line_total': round(line.quantity * item['unit_cost'], 2),
            'lead_time_days': item.get('lead_time_days', 14),
        })

    total_value = round(sum(li['line_total'] for li in line_items), 2)
    if total_value > request.budget:
        raise HTTPException(status_code=400,
                            detail=f"Order total {total_value} exceeds budget {request.budget}")

    now = datetime.now().replace(microsecond=0)
    # The order is considered delivered when its slowest line arrives.
    lead_time_days = max(li['lead_time_days'] for li in line_items)
    order = {
        'id': str(len(restocking_orders) + 1),
        'order_number': f"RST-{now.year}-{len(restocking_orders) + 1:04d}",
        'status': 'Submitted',
        'created_at': now.isoformat(),
        'budget': request.budget,
        'total_value': total_value,
        'lead_time_days': lead_time_days,
        'expected_delivery': (now + timedelta(days=lead_time_days)).isoformat(),
        'items': line_items,
    }
    # Mutate in place: main.py and mock_data.py share this list object.
    restocking_orders.append(order)
    mock_data.save_restocking_orders()
    return order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
