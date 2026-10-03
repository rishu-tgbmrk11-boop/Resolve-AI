# app.py
import streamlit as st
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

from tools import search_faq, search_products, lookup_order, lookup_customer_orders

load_dotenv()

st.set_page_config(page_title="Resolve AI", page_icon="🎧", layout="centered")

@st.cache_resource
def get_agent_and_client():
    system_prompt = """
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
    
    agent = ai.Agent(
        name="SupportAgent",
        model="groq:openai/gpt-oss-120b",
        instructions=system_prompt,
        tools=[search_faq, search_products, lookup_order, lookup_customer_orders],
    )
    client = ai.Client()
    return agent, client

agent, client = get_agent_and_client()

# --- Sidebar for Test Data ---
with st.sidebar:
    st.header("🧪 Test Data Helper")
    st.caption("Click any query below to copy it, then paste it into the chat.")
    
    # --- Product Queries ---
    with st.expander("🛍️ Product Queries", expanded=True):
        st.markdown("**Stock & availability:**")
        st.code("Do you have a laptop in stock?", language=None)
        st.code("Is the smartphone available?", language=None)
        st.code("Do you have any home appliances?", language=None)
        st.markdown("**Pricing:**")
        st.code("How much does the laptop cost?", language=None)
        st.code("What is the price of the smartphone?", language=None)
        st.markdown("**Product details:**")
        st.code("Tell me about the clothing products", language=None)
        st.code("What is the warranty on the laptop?", language=None)
    
    # --- Order Queries ---
    with st.expander("📦 Order Queries"):
        st.markdown("**By Order ID:**")
        st.code("Check order ORD-1050", language=None)
        st.code("What is the status of ORD-1073?", language=None)
        st.code("Where is order ORD-1099?", language=None)
        st.markdown("**By Email:**")
        st.code("My email is grace.davis@example.com", language=None)
        st.code("Look up orders for frank.anderson@example.com", language=None)
        st.code("I don't know my order ID, my email is john.doe@example.com", language=None)
    
    # --- FAQ Queries ---
    with st.expander("❓ FAQ / Policy Queries"):
        st.markdown("**Returns & refunds:**")
        st.code("What is your return policy?", language=None)
        st.code("How do I return an item?", language=None)
        st.code("How long does a refund take?", language=None)
        st.markdown("**Payments:**")
        st.code("Which payment methods do you accept?", language=None)
        st.code("Is my payment secure?", language=None)
        st.markdown("**Shipping:**")
        st.code("How long does shipping take?", language=None)
        st.code("Do you ship internationally?", language=None)
    
    # --- Multi-Tool Tests (Advanced) ---
    with st.expander("🎯 Multi-Tool Tests (Advanced)"):
        st.caption("These queries force the agent to use 2+ tools in sequence.")
        st.code("My email is grace.davis@example.com. Where is my order and do you have laptops?", language=None)
        st.code("I want to return the smartphone I bought. What is the return policy?", language=None)
        st.code("Check order ORD-1050 and tell me the warranty on the product.", language=None)
    
    st.divider()
    st.caption("💡 Tip: Watch the terminal for `🔧 [TOOL] ...` messages to see which tool the agent chose.")

st.title("🎧 Resolve AI Support")
st.markdown("Ask me about our products, policies, or your order!")
st.divider()

# --- Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input ---
if prompt := st.chat_input("How can I help you today?"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Checking our systems..."):
            try:
                result = ai.Runner.run_sync(agent, prompt, client=client, max_turns=5)
                response = result.final_output if result.final_output else "I'm sorry, I couldn't find an answer."
            except Exception as e:
                response = f"⚠️ An error occurred: {e}"
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})