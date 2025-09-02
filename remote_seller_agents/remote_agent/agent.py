"""
Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from pydantic import BaseModel
import uuid
from crewai import Agent, Crew, Task, Process
from crewai.tools import tool
from dotenv import load_dotenv
import litellm
import os

# --- Configuration ---
load_dotenv()

# --- Data Models for the Tool ---
class OrderItem(BaseModel):
    name: str
    quantity: int
    price: int

class Order(BaseModel):
    order_id: str
    status: str
    order_items: list[OrderItem]


# --- Agent Tool Definition ---
@tool("create_order")
def create_burger_order(order_items: list[OrderItem]) -> str:
    """Creates a new burger order with the given order items."""
    try:
        order_id = str(uuid.uuid4())
        order = Order(order_id=order_id, status="created", order_items=order_items)
        print(f"=== Order created: {order} ===")
        return f"Order {order.model_dump_json()} has been created"
    except Exception as e:
        print(f"Error creating order: {e}")
        return f"Error creating order: {e}"


# --- The Agent Logic ---
class BurgerSellerAgent:
    TaskInstruction = """
# INSTRUCTIONS
You are a specialized assistant for a burger store. Your sole purpose is to answer questions about the burger menu and prices, and to handle order creation. If the user asks about anything else, politely state that you can only assist with burger-related queries.

# CONTEXT
Received user query: {user_prompt}
Session ID: {session_id}

Provided below is the available burger menu and its related price:
- Classic Cheeseburger: IDR 85K
- Double Cheeseburger: IDR 110K
- Spicy Chicken Burger: IDR 80K
- Spicy Cajun Burger: IDR 85K

# RULES
- When creating an order:
  1. Always confirm the order items and total price with the user first.
  2. Use the `create_burger_order` tool to create the order.
  3. Finally, respond with the detailed ordered items, price breakdown, total, and the new order ID.
- Do not make up menu items or prices.
"""
    SUPPORTED_CONTENT_TYPES = [
        "text/plain",
        "application/json",
    ]
    
    def __init__(self):
        # Initialize the agent and model once to reuse them
        model = litellm.completion
        self.burger_agent = Agent(
            role="Burger Seller Agent",
            goal="Help users understand the burger menu and create orders.",
            backstory="You are an expert and helpful burger seller agent.",
            verbose=True,
            allow_delegation=False,
            tools=[create_burger_order],
            llm=model,
            model_name="azure/gpt-4.1"
        )
        print("Burger Seller Agent initialized for Azure OpenAI.")

    def invoke(self, query: str, session_id: str) -> str:
        agent_task = Task(
            description=self.TaskInstruction,
            agent=self.burger_agent,
            expected_output="A helpful response to the user, either answering a question or confirming an order.",
        )
        crew = Crew(
            tasks=[agent_task],
            agents=[self.burger_agent],
            verbose=True,
            process=Process.sequential,
        )

        inputs = {"user_prompt": query, "session_id": session_id}
        response = crew.kickoff(inputs=inputs)
        return response
