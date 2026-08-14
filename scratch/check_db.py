import sqlite3

def check_db():
    conn = sqlite3.connect("uretim_asistanim.db")
    cursor = conn.cursor()
    
    print("--- PRODUCTION LINES ---")
    cursor.execute("SELECT id, line_name, capacity, operator_name FROM production_lines")
    for r in cursor.fetchall():
        print(r)
        
    print("\n--- ORDERS ---")
    cursor.execute("SELECT id, order_no, item_no, quantity, production_line, status, estimated_delivery_date FROM orders")
    for r in cursor.fetchall():
        print(r)
        
    conn.close()

if __name__ == "__main__":
    check_db()
