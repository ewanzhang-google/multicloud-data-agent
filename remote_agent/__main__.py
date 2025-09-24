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

from a2a.types import AgentCapabilities, AgentSkill, AgentCard
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from agent import ProductSellerAgent
from agent_executor import ProductSellerAgentExecutor
import uvicorn
from dotenv import load_dotenv
import logging
import os
import click

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", "host", default="0.0.0.0")
@click.option("--port", "port", default=10001)
def main(host, port):
    """Entry point for the A2A + CrewAI Product Seller Agent."""
    try:
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="get_product_details",
            name="Product Details Lookup Tool",
            description="Retrieves product details using a product ID from static inventory.",
            tags=["product lookup", "inventory"],
            examples=["What are the details for product 27837?"],
        )
        
        # --- CHANGE: Simplified and clarified how the public URL is determined ---
        # When deploying to Azure, set the AGENT_BASE_URL environment variable 
        # to the public URL of your Container App.
        agent_base_url = os.getenv("AGENT_BASE_URL")
        if not agent_base_url:
            agent_base_url = f"http://{host}:{port}"
            logger.warning(f"AGENT_BASE_URL not set, defaulting to local URL: {agent_base_url}")
        
        agent_card = AgentCard(
            name="product_seller_agent",
            description="Provides product details based on a product ID.",
            url=agent_base_url, 
            version="1.0.0",
            # Use the SUPPORTED_CONTENT_TYPES from the new agent class
            defaultInputModes=ProductSellerAgent.SUPPORTED_CONTENT_TYPES, 
            defaultOutputModes=ProductSellerAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=ProductSellerAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        logger.info(f"Starting server on {host}:{port}, advertising public URL: {agent_base_url}")
        uvicorn.run(server.build(), host=host, port=port)

    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
