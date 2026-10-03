# tools.py
import pandas as pd
import os

from email_utils import fetch_unread_emails, send_reply

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    faq_df = pd.read_csv(os.path.join(BASE_DIR, "data", "faq_question_answer_dataset.csv"))
    products_df = pd.read_csv(os.path.join(BASE_DIR, "data", "products.csv"))
    orders_df = pd.read_csv(os.path.join(BASE_DIR, "data", "orders.csv"))
except FileNotFoundError as e:
    print(f"⚠️ Warning: Dataset missing. Error: {e}")


# ─────────────────────────────────────────────
# EXISTING TOOLS (unchanged)
# ─────────────────────────────────────────────

def search_faq(query: str) -> str:
    """
    Search the FAQ knowledge base for answers to policy, shipping, or account questions.
    Use this for questions about returns, refunds, payments, shipping, or store policies.
    """
    print(f"\n🔧 [TOOL] search_faq(query='{query}')")
    query_lower = query.lower()

    matches = faq_df[
        faq_df['Question'].str.lower().str.contains(query_lower, na=False) |
        faq_df['Answer'].str.lower().str.contains(query_lower, na=False) |
        faq_df['Keywords'].astype(str).str.lower().str.contains(query_lower, na=False)
    ].head(2)

    if matches.empty:
        return "No relevant FAQ found."

    results = []
    for _, row in matches.iterrows():
        results.append(
            f"Category: {row['Category']}\n"
            f"Q: {row['Question']}\n"
            f"A: {row['Answer']}"
        )
    return "\n---\n".join(results)


def search_products(query: str) -> str:
    """
    Search the product inventory for pricing, availability, and specifications.
    Use this when a customer asks about a specific product, its price, or stock.
    """
    print(f"\n🔧 [TOOL] search_products(query='{query}')")
    query_lower = query.lower()

    matches = products_df[
        products_df['Product Name'].str.lower().str.contains(query_lower, na=False) |
        products_df['Product Description'].str.lower().str.contains(query_lower, na=False) |
        products_df['Product Category'].str.lower().str.contains(query_lower, na=False)
    ].head(3)

    if matches.empty:
        return f"No products found matching '{query}'."

    results = []
    for _, row in matches.iterrows():
        stock = row['Stock Quantity']
        status = "In Stock" if stock > 0 else "Out of Stock"
        results.append(
            f"Product: {row['Product Name']}\n"
            f"Price: ${row['Price']}\n"
            f"Status: {status} ({stock} units)\n"
            f"Category: {row['Product Category']}\n"
            f"Details: {row['Product Description']}\n"
            f"Ratings: {row['Product Ratings']}"
        )
    return "\n---\n".join(results)


def lookup_order(order_id: str) -> str:
    """
    Look up the status and details of a specific customer order by its order ID.
    Use this when a customer provides an Order ID (e.g., ORD-1050).
    """
    print(f"\n🔧 [TOOL] lookup_order(order_id='{order_id}')")
    query_id = order_id.upper().strip()

    match = orders_df[orders_df['order_id'].str.upper() == query_id]

    if match.empty:
        return f"No order found with ID '{order_id}'."

    row = match.iloc[0]
    tracking = row['tracking_number'] if pd.notna(row['tracking_number']) else "Not yet assigned"

    return (
        f"Order ID: {row['order_id']}\n"
        f"Customer: {row['customer_name']} ({row['customer_email']})\n"
        f"Order Date: {row['order_date']}\n"
        f"Status: {row['status']}\n"
        f"Tracking: {tracking}\n"
        f"Total: ${row['total_amount']}"
    )


def lookup_customer_orders(email: str) -> str:
    """
    Look up all orders associated with a specific customer email address.
    Use this when a customer mentions 'my order' but does not provide an order ID.
    """
    print(f"\n🔧 [TOOL] lookup_customer_orders(email='{email}')")
    query_email = email.lower().strip()

    matches = orders_df[orders_df['customer_email'].str.lower() == query_email]

    if matches.empty:
        return f"No orders found for email '{email}'. Please verify the email address."

    results = []
    for _, row in matches.iterrows():
        results.append(
            f"Order: {row['order_id']} | Date: {row['order_date']} | "
            f"Status: {row['status']} | Total: ${row['total_amount']}"
        )
    return "\n---\n".join(results)


# ─────────────────────────────────────────────
# NEW EMAIL TOOLS
# ─────────────────────────────────────────────

def get_new_emails() -> str:
    """
    Fetch all unread emails from the customer support inbox.
    Use this when you need to check for new customer inquiries that arrived by email.
    """
    print(f"\n🔧 [TOOL] get_new_emails()")
    emails = fetch_unread_emails()

    if not emails:
        return "No new emails in the inbox."

    formatted = [f"Found {len(emails)} unread email(s):\n"]
    for e in emails:
        formatted.append(
            f"--- EMAIL ---\n"
            f"From: {e['from']}\n"
            f"Subject: {e['subject']}\n"
            f"Body:\n{e['body']}\n"
        )
    return "\n".join(formatted)


def send_email_reply(to_address: str, original_subject: str, reply_body: str) -> str:
    """
    Send a reply email to a customer.
    Use this AFTER you have composed the final answer using the other tools.
    'to_address' should be the customer's email (extracted from the 'From' field).
    'original_subject' is the subject of the customer's email (for threading).
    'reply_body' is your composed response text.
    """
    print(f"\n🔧 [TOOL] send_email_reply(to='{to_address}')")
    success = send_reply(to_address, original_subject, reply_body)

    if success:
        return f"✅ Reply sent to {to_address}."
    else:
        return f"❌ Failed to send reply to {to_address}. Check email credentials."