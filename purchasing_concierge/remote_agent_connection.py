from typing import Callable

import httpx

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    SendMessageRequest,
    SendMessageResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
)
from uuid import uuid4
from dotenv import load_dotenv
import json
from typing import Any
from a2a.client.errors import (
    A2AClientHTTPError,
    A2AClientJSONError,
    A2AClientTimeoutError,
)
from a2a.client.middleware import ClientCallContext
import requests

import google.oauth2.id_token
import google.auth.transport.requests

load_dotenv()

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


def _send_request(
    self,
    rpc_request_payload: dict[str, Any],
    http_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Sends a non-streaming JSON-RPC request to the agent with Google ID Token authentication.
    """
    
    # 1. Fetch Google ID Token for authentication
    try:
        # Request object for fetching token
        auth_request = google.auth.transport.requests.Request()
        
        # self.url is the target audience (REMOTE_SELLER_AGENT_URL)
        id_token = google.oauth2.id_token.fetch_id_token(
            auth_request, audience=self.url
        )
        
        # Prepare the Authorization header
        auth_headers = {"Authorization": f"Bearer {id_token}"}
    except Exception as e:
        # Fail immediately if token fetching is the issue
        raise A2AClientHTTPError(
            500, f"Failed to fetch ID Token for A2A request: {e}"
        ) from e

    # 2. Merge headers with any provided http_kwargs
    merged_http_kwargs = http_kwargs or {}
    
    # Ensure any existing headers are preserved and inject our auth header
    merged_http_kwargs["headers"] = merged_http_kwargs.get("headers", {})
    merged_http_kwargs["headers"].update(auth_headers)

    # 3. Send the request using the synchronous 'requests' library
    try:
        response = requests.post(
            self.url,
            json=rpc_request_payload,
            **merged_http_kwargs,
        )
        # Will raise requests.HTTPError for 4xx/5xx status codes (including 401/403)
        response.raise_for_status()
        
        return response.json()
    except requests.Timeout as e:
        # Catch requests library timeout
        raise A2AClientTimeoutError("Client Request timed out") from e
    except requests.HTTPError as e:
        # Catch HTTP error (this is where 401/403 errors will now be caught)
        raise A2AClientHTTPError(e.response.status_code, str(e)) from e
    except json.JSONDecodeError as e:
        # Catch JSON decoding error
        raise A2AClientJSONError(str(e)) from e
    except requests.RequestException as e:
        # Catch general requests network communication error
        raise A2AClientHTTPError(503, f"Network communication error: {e}") from e


def send_message(
    self,
    request: SendMessageRequest,
    *,
    http_kwargs: dict[str, Any] | None = None,
    context: ClientCallContext | None = None,
) -> SendMessageResponse:
    """Sends a non-streaming message request to the agent.

    Args:
        request: The `SendMessageRequest` object containing the message and configuration.
        http_kwargs: Optional dictionary of keyword arguments to pass to the
            underlying httpx.post request.
        context: The client call context.

    Returns:
        A `SendMessageResponse` object containing the agent's response (Task or Message) or an error.

    Raises:
        A2AClientHTTPError: If an HTTP error occurs during the request.
        A2AClientJSONError: If the response body cannot be decoded as JSON or validated.
    """
    if not request.id:
        request.id = str(uuid4())

    response_data = self._send_request(
        request.model_dump(mode="json", exclude_none=True), http_kwargs
    )
    return SendMessageResponse.model_validate(response_data)


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard, agent_url: str):
        print(f"agent_card: {agent_card}")
        print(f"agent_url: {agent_url}")
        self._httpx_client = httpx.AsyncClient(timeout=30)
        self.agent_client = A2AClient(self._httpx_client, agent_card, url=agent_url)

        # Replace the original method with our custom implementation
        # NOTE: This is a temporary workaround for issue in httpx event closed
        self.agent_client._send_request = _send_request.__get__(self.agent_client)
        self.agent_client.send_message = send_message.__get__(self.agent_client)

        self.card = agent_card

    def get_agent(self) -> AgentCard:
        return self.card

    def send_message(self, message_request: SendMessageRequest) -> SendMessageResponse:
        return self.agent_client.send_message(message_request)
