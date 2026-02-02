# Copyright 2026 UCP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""UCP."""

import json
import re
from typing import Any
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import AgentExtension, DataPart, Part, TextPart
from a2a.utils import (
    get_data_parts,
    new_agent_parts_message,
    new_agent_text_message,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from ucp_sdk.models.schemas.shopping.types.payment_instrument import (
    PaymentInstrument,
)
from ucp_sdk.models.schemas.ucp import ResponseCheckout as UcpMetadata
from .constants import (
    A2A_UCP_EXTENSION_URL,
    ADK_EXTENSIONS_STATE_KEY,
    ADK_LATEST_TOOL_RESULT,
    ADK_PAYMENT_STATE,
    ADK_UCP_METADATA_STATE,
    UCP_AGENT_HEADER,
    UCP_PAYMENT_DATA_KEY,
    UCP_RISK_SIGNALS_KEY,
)
from .ucp_profile_resolver import ProfileResolver


class UcpRequestProcessor:
    """Handle UCP-specific request processing."""

    def __init__(self, profile_resolver: ProfileResolver):
        """Initialize the UCP request processor.

        Args:
            profile_resolver: The profile resolver instance.

        """
        self.profile_resolver = profile_resolver

    def prepare_ucp_metadata(self, context: RequestContext) -> UcpMetadata:
        """Prepare UCP metadata from the request context.

        Args:
            context: The request context.

        Returns:
            UcpMetadata: The prepared UCP metadata.

        Raises:
            ValueError: If required headers or profiles are missing.

        """
        if A2A_UCP_EXTENSION_URL not in context.requested_extensions:
            raise ValueError("UCP Extension is required for this agent")

        headers = context.call_context.state.get("headers")  # type: ignore

        ucp_agent_header_key = next(
            (key for key in headers if key.lower() == UCP_AGENT_HEADER.lower()),
            None,
        )

        if not ucp_agent_header_key:
            raise ValueError("UCP-Agent should be present in request headers")

        ucp_agent_header_value = headers[ucp_agent_header_key]

        match = re.search(r'profile="([^"]*)"', ucp_agent_header_value)
        if not match or not match.group(1):
            raise ValueError(
                "Client profile URL is missing or empty in UCP-Agent header"
            )

        client_profile_url = match.group(1)
        client_profile_metadata = self.profile_resolver.resolve_profile(
            client_profile_url
        )
        return self.profile_resolver.get_ucp_metadata(client_profile_metadata)


class ADKAgentExecutor(AgentExecutor):
    """ADK agent executor implementation."""

    def __init__(self, agent, extensions: list[AgentExtension]):
        """Initialize a generic ADK agent executor.

        Args:
            agent: The ADK agent instance.
            extensions: List of agent extensions to be used.

        """
        self.agent = agent
        self.runner = Runner(
            app_name=agent.name,
            agent=agent,
            session_service=InMemorySessionService(),
        )
        self.extensions = extensions or []
        self.profile_resolver = ProfileResolver()
        self.ucp_processor = UcpRequestProcessor(self.profile_resolver)

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel the execution of a specific task.

        Args:
            context: The request context.
            event_queue: The event queue.

        """
        raise NotImplementedError(
            "Cancellation is not implemented for ADKAgentExecutor."
        )

    async def _get_or_create_session(
        self, context: RequestContext, user_id: str
    ):
        """Get an existing session or create a new one.

        Args:
            context: The request context.
            user_id: The ID of the user.

        Returns:
            The session object.

        """
        session = await self.runner.session_service.get_session(
            app_name=self.agent.name,
            user_id=user_id,
            session_id=context.context_id,  # type: ignore
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.agent.name,
                user_id=user_id,
                session_id=context.context_id,  # type: ignore
            )

        return session

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the agent for the given context.

        Args:
            context: The request context.
            event_queue: The event queue.

        """
        if not context.message:
            raise ValueError("Message should be present in request context")

        self._activate_extensions(context)
        ucp_metadata = self.ucp_processor.prepare_ucp_metadata(context)

        query, payment_data = self._prepare_input(context)

        user_id: str = context.context_id  # random guest id for the session

        try:
            session = await self._get_or_create_session(context, user_id)
            result_parts = await self._run_agent_and_process_response(
                user_id, session.id, query, context, ucp_metadata, payment_data
            )
            await event_queue.enqueue_event(
                new_agent_parts_message(result_parts, context.context_id, None)
            )

        except Exception as e:
            await event_queue.enqueue_event(
                new_agent_text_message(
                    f"Error: {context.context_id} - {str(e)}",
                )
            )

    def _activate_extensions(self, context: RequestContext):
        """Activate extensions based on the request context.

        Args:
            context: The request context.

        """
        if context.requested_extensions:
            for ext in self.extensions:
                if ext.uri in context.requested_extensions:
                    context.add_activated_extension(ext.uri)

    def _prepare_input(
        self,
        context: RequestContext,
    ) -> tuple[str, dict | None]:
        """Prepare user query and payment mandate from the request context.

        Args:
            context: The request context.

        Returns:
            tuple[str, dict | None]: The query and payment data.

        """
        query = context.get_user_input()
        data_list = get_data_parts(context.message.parts)  # type: ignore
        payment_payload: dict[str, Any] = {}
        payment_keys = [UCP_PAYMENT_DATA_KEY, UCP_RISK_SIGNALS_KEY]

        # extract payment data related structured inputs
        # for processing by tools from the state
        for data_part in data_list:
            for key in payment_keys:
                if key in data_part:
                    value = data_part.pop(key)
                    if key == UCP_PAYMENT_DATA_KEY:
                        payment_payload[key] = (
                            PaymentInstrument.model_validate(value)
                        )
                    else:
                        payment_payload[key] = value

            if data_part:
                query += "\n" + json.dumps(data_part)

        return query, payment_payload or None

    def _build_initial_state_delta(
        self,
        context: RequestContext,
        ucp_metadata: UcpMetadata,
        payment_data: dict | None,
    ) -> dict:
        """Build the initial state delta for the agent run.

        Args:
            context: The request context.
            ucp_metadata: The UCP metadata.
            payment_data: The payment data.

        Returns:
            dict: The initial state delta.

        """
        return {
            ADK_UCP_METADATA_STATE: ucp_metadata,
            ADK_EXTENSIONS_STATE_KEY: context.requested_extensions,
            ADK_PAYMENT_STATE: payment_data,
            ADK_LATEST_TOOL_RESULT: None,
        }

    async def _run_agent_and_process_response(
        self,
        user_id: str,
        session_id: str,
        query: str,
        context: RequestContext,
        ucp_metadata: UcpMetadata,
        payment_data: dict | None,
    ) -> list[Part]:
        """Run the ADK agent and processes the response.

        Args:
            user_id: The ID of the user.
            session_id: The ID of the session.
            query: The user query.
            context: The request context.
            ucp_metadata: The UCP metadata.
            payment_data: The payment data.

        Returns:
            list[Part]: The response parts.

        """
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )

        state_delta = self._build_initial_state_delta(
            context, ucp_metadata, payment_data
        )
        result_parts: list[Part] = []

        final_events: list = []

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
            state_delta=state_delta,
        ):
            if event.is_final_response() or len(final_events) > 0:
                final_events.append(event)

        for final_event in final_events:
            response_text = ""
            for part in final_event.content.parts:  # type: ignore
                result_part = self._process_event_part(part)
                if isinstance(result_part, DataPart):
                    result_parts.append(Part(root=result_part))
                elif isinstance(result_part, TextPart):
                    response_text += result_part.text

            if response_text and not any(
                isinstance(p.root, DataPart) for p in result_parts
            ):
                result_parts.append(Part(root=TextPart(text=response_text)))

        return result_parts

    def _process_event_part(self, part) -> TextPart | DataPart | None:
        """Process a part from a runner event and return a result part.

        Args:
            part: The part to process.

        Returns:
            TextPart | DataPart | None: The result part, or None.

        """
        if part.function_response and part.function_response.response:
            result = part.function_response.response.get("result")
            if isinstance(result, dict):
                return DataPart(data=result)
            if isinstance(result, str):
                return TextPart(text=result)

        if hasattr(part, "text") and part.text:
            return TextPart(text=part.text)

        return None
