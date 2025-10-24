# Multicloud Data Agent Demo

This demo shows how to enable multicloud data agent communication between purchasing concierge agent with the remote product seller agents using A2A Python SDK. It demonstrates for a Retailer and a CPG to exchange / trade information based on the latest product catalogue, while also reacting to the latest consumer purchase trends in order to determine the supply chain / product strategy.

The product seller agent is deployed in Azure Container Apps using crewai framework and openai models, and the purchasing concierge agent is deployed in GCP Agent Engine using adk framework and gemini models.

## Prerequisites in GCP

- If you are executing this project from your local IDE, Login to Gcloud using CLI with the following command :

    ```shell
    gcloud auth application-default login
    ```

- Enable the following APIs

    ```shell
    gcloud services enable aiplatform.googleapis.com 
    ```

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/) dependencies and prepare the python env

    ```shell
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv python install 3.12
    uv sync --frozen
    ```

## How to Run

### Deploy the Remote Product Seller Agent in Azure

First, we need to run the remote product seller agents which will serve the A2A Server.

1. Define key varibales for the container app
```bash
git clone https://github.com/ewanzhang-google/purchasing-concierge-a2a.git

export RESOURCE_GROUP="product-agent-rg"
export LOCATION="centralus"
export ACR_NAME="productagentacr123" # Must be globally unique
export IMAGE_NAME="product-agent"
export IMAGE_TAG="v1"
```

2. Create resource group, artifact registry and build the container image
```bash
az group create --name $RESOURCE_GROUP --location $LOCATION

az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

az acr build --registry $ACR_NAME --image my-product-app:v1 .
```

3. Create container env and container app
```bash
az containerapp env create \
  --name ProductAgent-Env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

az containerapp create \
  --name product-seller-agent-app \
  --resource-group $RESOURCE_GROUP \
  --environment ProductAgent-Env \
  --image $ACR_NAME.azurecr.io/my-product-app:v10 \
  --target-port 8080 \
  --ingress external \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-identity system
```

4. Fill out the env variables for the container app
AZURE_API_KEY: 3y6IVGelvTthXrxYc9GJ2kXQIk8C3v6aXppdFpAVWxJERKFljRhOJQQJ99BHACYeBjFXJ3w3AAAAACOGh6e3
AZURE_API_BASE: https://amazingproject.openai.azure.com/
AZURE_API_VERSION: 2025-04-14
AGENT_BASE_URL: https://product-seller-agent-app.nicedune-ca40aa05.centralus.azurecontainerapps.io
AZURE_DEPLOYMENT_NAME: gpt-4.1

5. Make a note of the AGENT_URL and confirm it appears in agent.json as well.
```bash
AGENT_URL=$(az containerapp show --name product-seller-agent-app --resource-group $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)

curl "https://$AGENT_URL/.well-known/agent.json"
```



### Deploy the Purchasing Concierge Agent in GCP

Second we will run our A2A client capabilities owned by purchasing concierge agent.

1. Create the staging bucket first

    ```bash
    gcloud storage buckets create gs://purchasing-concierge-{your-project-id} --location=us-central1
    ```

2. Go back to demo root directory (where `purchasing_concierge` directory is located). Copy the `purchasing_concierge/.env.example` to `purchasing_concierge/.env`.
3. Fill in the required environment variables in the `.env` file. Substitute `GOOGLE_CLOUD_PROJECT` with your Google Cloud Project ID.
   And fill in the `REMOTE_AGENT_URL` with the URL of the remote product seller agent.

    ```bash
    git clone https://github.com/ewanzhang-google/purchasing-concierge-a2a.git
    
    GOOGLE_GENAI_USE_VERTEXAI=TRUE
    GOOGLE_CLOUD_PROJECT={your-project-id}
    GOOGLE_CLOUD_LOCATION=us-central1
    STAGING_BUCKET=gs://purchasing-concierge-{your-project-id}
    REMOTE_AGENT_URL={your-pizza-agent-url}
    ```

4. Deploy the purchasing concierge agent to agent engine

    ```bash
    uv sync --frozen
    uv run deploy_to_agent_engine.py
    ```

### Run the Chat Interface to Connect to Agent Engine

1. Update the `.env` file with the `AGENT_ENGINE_RESOURCE_NAME` which obtained from the previous step.

2. Run the Gradio app

```bash
uv sync --frozen
uv run purchasing_concierge_ui.py
```
