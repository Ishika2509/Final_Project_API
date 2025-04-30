readme_content = """
# Dosa Restaurant API

A FastAPI-based REST API backend for managing customers, menu items, and orders at a Dosa restaurant.

## 📦 Project Overview

This project uses:
- **FastAPI** for the API framework
- **SQLite** (`db.sqlite`) as the database
- **Pydantic** for request validation
- Full CRUD functionality for:
  - Customers
  - Items
  - Orders

## 🗂 Directory Structure

.
├── db.sqlite            # SQLite database file (created after init)
├── init_db.py           # Script to create the database schema
├── main.py              # FastAPI app with all CRUD endpoints
├── example_orders.json  # Sample data (optional for testing)
├── customers.json       # Sample customer data (for reference)
├── items.json           # Sample item data (for reference)
├── README.md            # This documentation file


```bash
git clone https://github.com/Ishika2509/Final_Project_API.git
cd Final_Project_API
