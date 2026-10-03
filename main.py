# main.py
import os
from dotenv import load_dotenv
import aisuite as ai

# --- MONKEY PATCH: Fix Groq reasoning_content error ---
from aisuite.providers.groq_provider import GroqMessageConverter
_original_convert_request = GroqMessageConverter.convert_request

def _patched_convert_request(messages):
    transformed = _original_convert_request(messages)
    for msg in transformed:
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            msg.pop("reasoning_content", None)
    return transformed

GroqMessageConverter.convert_request = staticmethod(_patched_convert_request)
# --- END MONKEY PATCH ---

from tools import (
    search_faq, search_products, lookup_order, lookup_customer_orders,
    get_new_emails, send_email_reply
)

load_dotenv()

SYSTEM_PROMPT = """
You are a helpful, empathetic Customer Support Agent for an e-commerce store.

Tools available:
1. `search_faq(query)`: For policies, returns, refunds, payments, shipping, or store policies.
2. `search_products(query)`: For product prices, stock availability, or specifications.
3. `lookup_order(order_id)`: When a customer provides an Order ID (e.g., ORD-1050).
4. `lookup_customer_orders(email)`: When a customer mentions "my order" but doesn't give an ID. Ask for their email first.

Rules:
- If a customer asks about a product, use `search_products`.
- If they give an order ID, use `lookup_order`.
- If they don't have an order ID, ask for their email and use `lookup_customer_orders`.
- For policy/return/payment questions, use `search_faq`.
- Never make up prices or statuses. Always use the tools.
- Be polite, professional, and concise.
"""

def main():
    print("🎧 Resolve AI Terminal ready. Type 'quit' to exit.\n")
    
    client = ai.Client()
    agent = ai.Agent(
        name="SupportAgent",
        model="groq:openai/gpt-oss-120b",
        instructions=SYSTEM_PROMPT,
        tools=[
            search_faq, search_products, lookup_order, lookup_customer_orders,
            get_new_emails, send_email_reply
        ],
    )
    
    while True:
        query = input("Customer: ").strip()
        if not query or query.lower() == "quit":
            break
        
        print("\n🧠 Agent is thinking...")
        try:
            result = ai.Runner.run_sync(agent, query, client=client, max_turns=5)
            
            print("\n" + "="*60)
            print("🤖 Agent Response:")
            print("="*60)
            if result.final_output:
                print(result.final_output)
            else:
                print("Agent stopped without a final answer.")
            print()
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()