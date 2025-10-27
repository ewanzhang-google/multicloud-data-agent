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
import json
import uuid
from crewai import Agent, Crew, Task, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv
import litellm
import os

# --- Configuration ---
load_dotenv()

# --- Static Data Source ---
STATIC_PRODUCTS_JSON = """
[{"product_id": "27837", "cost": "14.22500004991889", "category": "Swim", "name": "Beach Rays Men\u0027s Cargo Pocket Boardshort", "brand": "Beach Rays", "retail_price": "25.0", "department": "Men", "sku": "AF1A4EA496C2D7D01D9D1EBD8D5C82F4", "distribution_center_id": "6"}, 
{"product_id": "25930", "cost": "12.649999978020787", "category": "Underwear", "name": "Hanes Men\u0027s 3 Pack Comfortblend Short Leg Boxer Brief", "brand": "Hanes", "retail_price": "25.0", "department": "Men", "sku": "F21C444A5DD33EEA45CE16801C289D23", "distribution_center_id": "3"}, 
{"product_id": "28953", "cost": "7.4298698834899071", "category": "Accessories", "name": "100% Silk Woven Gold Plaid Self-Tie Bow Tie", "brand": "TheTieBar", "retail_price": "17.989999771118164", "department": "Men", "sku": "7B889DA86FA368B083E6B41F1C879FA9", "distribution_center_id": "7"}, 
{"product_id": "24316", "cost": "31.156109792127609", "category": "Outerwear \u0026 Coats", "name": "Dickies - Fleece-Lined Hooded Nylon Jacket", "brand": "Dickies", "retail_price": "69.389999389648438", "department": "Men", "sku": "70A3E3E59BC61C8EB7ACFBBA1073980C", "distribution_center_id": "1"}, 
{"product_id": "20309", "cost": "7.32914969935119", "category": "Suits \u0026 Sport Coats", "name": "Allegra K Mens Stylish Solid Color Small Pocket Upper Button Closure Fall Blazer Gray S", "brand": "Allegra K", "retail_price": "16.469999313354492", "department": "Men", "sku": "B05F00551528BDA221276D01A40B7EF2", "distribution_center_id": "9"}, 
{"product_id": "12638", "cost": "4.4284999975934634", "category": "Intimates", "name": "Fashion Forms Low Back Straps", "brand": "Fashion Forms", "retail_price": "8.5", "department": "Women", "sku": "195D221C982E47EB58347E5D06CE3180", "distribution_center_id": "10"}, 
{"product_id": "4568", "cost": "96.668000105768442", "category": "Jeans", "name": "Joe\u0027s Jeans Women\u0027s Yasmin Skinny Jean", "brand": "Joe\u0027s Jeans", "retail_price": "169.0", "department": "Women", "sku": "BCFA8A783AAF938CDEF361634D5F9289", "distribution_center_id": "6"}, 
{"product_id": "24631", "cost": "5.8500000182539225", "category": "Socks", "name": "K. Bell Socks Men\u0027s Wide Mouth Shark", "brand": "K. Bell", "retail_price": "10.0", "department": "Men", "sku": "EB3CEE21198139FA6A21866D764CC4B8", "distribution_center_id": "5"}, 
{"product_id": "5433", "cost": "11.640959460911304", "category": "Pants \u0026 Capris", "name": "BKE Women\u0027s Casual Linen Cotton Natural Comfortable Pants", "brand": "BKE", "retail_price": "20.209999084472656", "department": "Women", "sku": "BF25356FD2A6E038F1A3A59C26687E80", "distribution_center_id": "1"}, 
{"product_id": "23456", "cost": "41.118000108748674", "category": "Shorts", "name": "Jet Lag Men\u0027s Take Off 3 Cargo Shorts", "brand": "Jet Lag", "retail_price": "89.0", "department": "Men", "sku": "ADCAEC3805AA912C0D0B14A81BEDB6FF", "distribution_center_id": "6"}]
"""
STATIC_PRODUCTS = json.loads(STATIC_PRODUCTS_JSON)

# --- Data Models for the Tool ---
class Product(BaseModel):
    product_id: str
    cost: str
    category: str
    name: str
    brand: str
    retail_price: str
    department: str
    sku: str
    distribution_center_id: str


# --- Agent Tool Definition ---
@tool("get_product_details")
def get_product_details(product_id: str) -> str:
    """
    Retrieves detailed information for a product using its ID from the static data source.
    Returns a JSON string of the product details or an error message if not found.
    """
    try:
        # Search the static list for the product_id
        product_data = next((p for p in STATIC_PRODUCTS if p["product_id"] == product_id), None)
        
        if product_data:
            # Convert float strings to float for calculation, then format the output
            cost = float(product_data.get("cost", 0))
            retail_price = float(product_data.get("retail_price", 0))
            
            # Format the output for the LLM
            return json.dumps({
                "product_id": product_data.get("product_id"),
                "name": product_data.get("name"),
                "brand": product_data.get("brand"),
                "category": product_data.get("category"),
                "department": product_data.get("department"),
                "retail_price": f"${retail_price:.2f}",
                "cost": f"${cost:.2f}",
                "sku": product_data.get("sku"),
            }, indent=2)
        else:
            return f"Product with ID {product_id} not found in the static inventory."
    except Exception as e:
        print(f"Error retrieving product details: {e}")
        return f"Error retrieving product details: {e}"


# --- The Agent Logic ---
class ProductSellerAgent:
    TaskInstruction = """
# INSTRUCTIONS
You are an expert **Product Seller Agent**. Your goal is to provide detailed information about products when given a specific product ID.

# CONTEXT
Received user query: {user_prompt}
Session ID: {session_id}

# RULES
- **Primary Function:** Use the `get_product_details` tool to look up product information whenever the user asks about a product and provides a specific product ID (e.g., "What is the price of product 27837?").
- **Response:** Provide a helpful, concise summary of the product's details, including its name, category, brand, and retail price.
- **Unavailable Product:** If the product is not found via the tool, inform the user that the product ID is invalid or not in stock.
- **Irrelevant Query:** If the user's query is not about finding product details by ID, politely state that you can only assist with product lookups using a product ID.
"""
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    
    def __init__(self):
        print("--- Azure Environment Variables ---")
        print(f"AZURE_API_KEY: {os.environ.get('AZURE_API_KEY')}")
        print(f"AZURE_API_BASE: {os.environ.get('AZURE_API_BASE')}")
        print(f"AZURE_API_VERSION: {os.environ.get('AZURE_API_VERSION')}")
        print("---------------------------------")

        model = litellm.completion
        
        self.product_agent = Agent(
            role="Product Seller Agent",
            goal="Provide product details when prompted with a product ID.",
            backstory="You are a specialized agent providing product lookup services.",
            verbose=True,
            allow_delegation=False,
            tools=[get_product_details],
            llm=LLM(model="azure/gpt-4.1") #add model information from the agent created in AI Foundry
        )
        print("Product Seller Agent initialized for Azure OpenAI.")

    def invoke(self, query: str, session_id: str) -> str:
        agent_task = Task(
            description=self.TaskInstruction,
            agent=self.product_agent,
            expected_output="A helpful response to the user, either answering a question or asking for the product ID.",
        )
        crew = Crew(
            tasks=[agent_task],
            agents=[self.product_agent],
            verbose=True,
            process=Process.sequential,
        )

        inputs = {"user_prompt": query, "session_id": session_id}
        response = crew.kickoff(inputs=inputs)
        return response
