"""
Testing from Gemini 2.5
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from crewai import Agent, Crew, Task, Process
from crewai.tools import tool
from dotenv import load_dotenv
import litellm
import os

# --- Configuration ---
# Load environment variables for local development. In Azure, these will be set in the service configuration.
load_dotenv()

# LiteLLM will automatically pick up Azure credentials from these standard environment variables:
# AZURE_API_BASE, AZURE_API_KEY, AZURE_API_VERSION
# So, we don't need to set them in the code.

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

# --- The Agent Logic (encapsulated in a class) ---
class BurgerSellerAgent:
    TaskInstruction = """
# INSTRUCTIONS
You are a specialized assistant for a burger store. Your sole purpose is to answer questions about the burger menu and prices, and to handle order creation. If the user asks about anything else, politely state that you can only assist with burger-related queries.

# CONTEXT
Received user query: {user_prompt}
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
    def __init__(self):
        model = litellm.completion
        self.burger_agent = Agent(
            role="Burger Seller Agent",
            goal="Help users understand the burger menu and create orders.",
            backstory="You are an expert and helpful burger seller agent.",
            verbose=True,
            allow_delegation=False,
            tools=[create_burger_order],
            llm=model,
            # ** CHANGE HERE: Point to your Azure OpenAI model deployment **
            model_name="azure/your-gpt-deployment-name" 
        )
        print("Burger Seller Agent initialized.")

    def invoke(self, query: str) -> str:
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
        inputs = {"user_prompt": query}
        response = crew.kickoff(inputs=inputs)
        return response

# --- FastAPI Web Application ---
app = FastAPI(title="Burger Agent API")
burger_agent_instance = BurgerSellerAgent()

class InvokeRequest(BaseModel):
    query: str

class InvokeResponse(BaseModel):
    reply: str

@app.post("/invoke", response_model=InvokeResponse)
async def handle_invoke(request: InvokeRequest):
    """Receives a query and returns the agent's response."""
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        print(f"Invoking agent with query: '{request.query}'")
        agent_reply = burger_agent_instance.invoke(query=request.query)
        return InvokeResponse(reply=agent_reply)
    except Exception as e:
        print(f"An error occurred during agent invocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """A simple health check endpoint."""
    return {"status": "ok"}
