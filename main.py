from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Dosa Restaurant API")

DB_PATH = "db.sqlite"

# --- Pydantic Models ---

class Customer(BaseModel):
    name: str
    phone: str

class CustomerInDB(Customer):
    id: int

# --- DB Helper ---

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- CRUD Endpoints for Customers ---

@app.post("/customers", response_model=CustomerInDB)
def create_customer(customer: Customer):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)",
                       (customer.name, customer.phone))
        conn.commit()
        customer_id = cursor.lastrowid
        return {**customer.dict(), "id": customer_id}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Phone number must be unique.")
    finally:
        conn.close()

@app.get("/customers/{id}", response_model=CustomerInDB)
def get_customer(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Customer not found.")

@app.put("/customers/{id}", response_model=CustomerInDB)
def update_customer(id: int, customer: Customer):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET name = ?, phone = ? WHERE id = ?",
                   (customer.name, customer.phone, id))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Customer not found.")
    conn.close()
    return {**customer.dict(), "id": id}

@app.delete("/customers/{id}")
def delete_customer(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Customer not found.")
    conn.close()
    return {"message": "Customer deleted."}

# --- Pydantic Models for Items and Orders ---

class Item(BaseModel):
    name: str
    price: float

class ItemInDB(Item):
    id: int

class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int = 1

class Order(BaseModel):
    customer_id: int
    timestamp: int
    notes: str = ""
    items: list[OrderItem]

class OrderInDB(BaseModel):
    id: int
    customer_id: int
    timestamp: int
    notes: str
    items: list[OrderItem]

# --- CRUD Endpoints for Items ---

@app.post("/items", response_model=ItemInDB)
def create_item(item: Item):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO items (name, price) VALUES (?, ?)", (item.name, item.price))
        conn.commit()
        return {**item.dict(), "id": cursor.lastrowid}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Item name must be unique.")
    finally:
        conn.close()

@app.get("/items/{id}", response_model=ItemInDB)
def get_item(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Item not found.")

@app.put("/items/{id}", response_model=ItemInDB)
def update_item(id: int, item: Item):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET name = ?, price = ? WHERE id = ?", (item.name, item.price, id))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found.")
    conn.close()
    return {**item.dict(), "id": id}

@app.delete("/items/{id}")
def delete_item(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found.")
    conn.close()
    return {"message": "Item deleted."}

# --- CRUD Endpoints for Orders ---

@app.post("/orders", response_model=OrderInDB)
def create_order(order: Order):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO orders (customer_id, timestamp, notes) VALUES (?, ?, ?)",
        (order.customer_id, order.timestamp, order.notes)
    )
    order_id = cursor.lastrowid

    # Add items
    for item in order.items:
        # Try to get existing item by name
        cursor.execute("SELECT id FROM items WHERE name = ?", (item.name,))
        row = cursor.fetchone()
        if row:
            item_id = row["id"]
        else:
            cursor.execute("INSERT INTO items (name, price) VALUES (?, ?)", (item.name, item.price))
            item_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO order_items (order_id, item_id, quantity) VALUES (?, ?, ?)",
            (order_id, item_id, item.quantity)
        )

    conn.commit()
    conn.close()
    return {**order.dict(), "id": order_id}

@app.get("/orders/{id}", response_model=OrderInDB)
def get_order(id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE id = ?", (id,))
    order_row = cursor.fetchone()
    if not order_row:
        raise HTTPException(status_code=404, detail="Order not found.")

    cursor.execute("""
        SELECT i.name, i.price, oi.quantity
        FROM order_items oi
        JOIN items i ON oi.item_id = i.id
        WHERE oi.order_id = ?
    """, (id,))
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "id": order_row["id"],
        "customer_id": order_row["customer_id"],
        "timestamp": order_row["timestamp"],
        "notes": order_row["notes"],
        "items": items
    }

@app.put("/orders/{id}", response_model=OrderInDB)
def update_order(id: int, order: Order):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("UPDATE orders SET customer_id = ?, timestamp = ?, notes = ? WHERE id = ?",
                   (order.customer_id, order.timestamp, order.notes, id))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Delete old items
    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (id,))

    for item in order.items:
        cursor.execute("SELECT id FROM items WHERE name = ?", (item.name,))
        row = cursor.fetchone()
        if row:
            item_id = row["id"]
        else:
            cursor.execute("INSERT INTO items (name, price) VALUES (?, ?)", (item.name, item.price))
            item_id = cursor.lastrowid
        cursor.execute("INSERT INTO order_items (order_id, item_id, quantity) VALUES (?, ?, ?)",
                       (id, item_id, item.quantity))

    conn.commit()
    conn.close()
    return {**order.dict(), "id": id}

@app.delete("/orders/{id}")
def delete_order(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Order not found.")
    conn.close()
    return {"message": "Order deleted."}
