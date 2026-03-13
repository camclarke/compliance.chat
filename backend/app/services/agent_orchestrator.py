import os
import logging
from typing import Optional
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System Prompt — Global Type Approval Specialist
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an elite Global Type Approval (GTA) Compliance Specialist with deep \
expertise in wireless telecommunications certification for the international market. You have mastered \
the regulatory frameworks of the FCC (USA), ISED (Canada), CE/RED (EU), UKCA (UK), ANATEL (Brazil), \
IFETEL/NOM (Mexico), SRRC (China), MIC (Japan), KCC (South Korea), RCM (Australia/NZ), BIS (India), \
and all major global certification regimes.

## YOUR RESEARCH METHODOLOGY
When a user asks a compliance question, you MUST execute the following multi-step research loop \
using Bing Search before composing your answer:

1. **Identify the exact regulatory body and standard.** Search for the primary official regulatory \
   text (e.g., "FCC Part 15 rules", "ANATEL Resolução 715", "NOM-121-SCT1-2009 full text").
2. **Search for the latest amendment or update.** Regulations change frequently. Always search \
   "[regulation name] [current year] amendment update" to confirm currency.
3. **Verify with a certification body or standards reference.** Cross-reference with a recognised \
   test lab (UL, TÜV, SGS, Intertek, Element) or standards body (ETSI, IEEE, ITU) source.
4. **Synthesize a structured ruling.** Combine all findings into a definitive compliance analysis \
   using the output format below.

## YOUR OUTPUT FORMAT
Always structure answers using this exact format:

**Jurisdiction:** [Country / Region]
**Regulatory Body:** [FCC / ANATEL / IFETEL / etc.]
**Applicable Standard:** [Part 15 / Resolution 715 / NOM-xxx / etc.]
**Specific Requirement:** [Precise technical or procedural requirement]
**Effective Date / Last Amended:** [Date if found]
**Citation:** [Direct URL to official regulatory text or government source]
**Confidence Level:** HIGH / MEDIUM / LOW
  — HIGH = primary government source found via search
  — MEDIUM = recognised secondary source (test lab, standards body)
  — LOW = inference only, no direct source located

## HALLUCINATION PREVENTION — STRICT PROTOCOL
- You MUST cite a real, verifiable URL from Bing for every factual regulatory claim.
- If Bing search returns no results for a specific regulation, you MUST state:
  "I could not locate a verified current regulatory source for this requirement. \
   Please consult [regulatory body] directly at [official website]."
- NEVER fabricate regulation numbers, power limits, bandwidth allocations, or certification fees.
- NEVER present training-data knowledge as current fact without live Bing verification — \
  regulations change and your training data may be outdated.
- If search results conflict, present both findings and clearly note the discrepancy.

## DOMAIN EXPERTISE
- **Radio/RF:** FCC Part 15 (B/C/D/E), Part 22/24/27/90; ISED RSS-102/210/Gen; CE RED 2014/53/EU; \
  ETSI EN 300 328, EN 301 511, EN 301 893
- **EMC:** FCC Part 15B; CISPR 32; EN 55032; IEC 61000 series; VCCI (Japan); KN 32 (Korea)
- **Safety:** IEC 62368-1; UL 62368-1; EN 62368-1; CSA C22.2
- **LATAM:** ANATEL — Resolução 715, Ato 10650; IFETEL — NOM-121-SCT1, NOM-208-SCFI; \
  SUBTEL (Chile); ENACOM (Argentina)
- **Asia:** SRRC (China) type approval; MIC (Japan) 技術基準適合証明; KCC (Korea) KC Mark; \
  BIS (India) CRS
- **Multimodal Products:** Devices with multiple radio technologies (BT + Wi-Fi + LTE) requiring \
  simultaneous multi-band certification across jurisdictions"""

# ---------------------------------------------------------------------------
# Module-level Bing tools cache — resolved once per process lifetime
# ---------------------------------------------------------------------------
_cached_bing_definitions: Optional[list] = None
_bing_cache_populated: bool = False


class AgentResult:
    def __init__(self, text: str, usage_metadata: dict, sources: list = None):
        self.text = text
        self.metadata = usage_metadata
        self.sources = sources or []

    def __str__(self):
        return self.text


async def create_kernel() -> Optional[AIProjectClient]:
    """
    Initializes AIProjectClient.
    Name kept as create_kernel for backward compatibility with chat.py dependency injection.
    """
    endpoint = os.getenv("PROJECT_ENDPOINT")
    if not endpoint:
        logger.error("Missing PROJECT_ENDPOINT in environment variables.")
        return None

    client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )
    logger.info("Successfully initialized AIProjectClient.")
    return client


async def _resolve_bing_tools(client: AIProjectClient) -> list:
    """
    Scans the project's connections for a Bing Search connection and returns the
    BingGroundingTool definitions. Result is cached for the process lifetime to
    avoid repeated connection-list scans on every request.
    """
    global _cached_bing_definitions, _bing_cache_populated

    if _bing_cache_populated:
        return _cached_bing_definitions or []

    try:
        async for c in client.connections.list():
            conn_type = getattr(c, "connection_type", "") or ""
            if "bing" in c.name.lower() or conn_type.lower() == "bing_search_connection":
                bing_connection = await client.connections.get(connection_name=c.name)
                bing = BingGroundingTool(bing_connection)
                _cached_bing_definitions = bing.definitions
                _bing_cache_populated = True
                logger.info(f"Bing Grounding Tool cached from connection: {bing_connection.name}")
                return _cached_bing_definitions
    except Exception as e:
        logger.warning(f"Failed to resolve Bing connection: {e}")

    _bing_cache_populated = True  # Don't retry on every request if no connection exists
    logger.warning("No Bing connection found. Agent will run without live search.")
    return []


def _extract_text_and_citations(message) -> tuple:
    """
    Extracts the plain-text response and a de-duplicated list of citation URLs
    from Bing grounding annotations on an Assistants API message.
    """
    text_parts = []
    sources = []
    seen = set()

    for block in message.content:
        if block.type != "text":
            continue
        text_parts.append(block.text.value)
        for annotation in getattr(block.text, "annotations", []):
            if annotation.type == "url_citation":
                url = getattr(annotation.url_citation, "url", None)
                if url and url not in seen:
                    seen.add(url)
                    sources.append(url)

    return "".join(text_parts), sources


async def process_chat_message(
    client: AIProjectClient,
    message: str,
    file_content: bytes = None,
    file_name: str = None,
    file_content_type: str = None,
    history: list = None,
) -> Optional[AgentResult]:
    """
    Processes a user's compliance query using Azure AI Agent Service with Bing Grounding.

    Args:
        client:   Initialised AIProjectClient.
        message:  The user's current query.
        history:  List of prior conversation turns as {"role": str, "content": str} dicts,
                  oldest-first. The agent replays these into the thread for full context.
    """
    if not client:
        logger.error("AIProjectClient not initialized.")
        return None

    try:
        tool_definitions = await _resolve_bing_tools(client)

        openai_client = await client.get_openai_client(api_version="2024-05-01-preview")

        agent = await openai_client.beta.assistants.create(
            model="gpt-4o",
            name="ComplianceAgent",
            instructions=SYSTEM_PROMPT,
            tools=tool_definitions,
        )
        logger.info(f"Created agent {agent.id} with {len(tool_definitions)} tool(s).")

        try:
            thread = await openai_client.beta.threads.create()

            # Replay conversation history so the agent has full multi-turn context.
            for turn in (history or []):
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if content and role in ("user", "assistant"):
                    try:
                        await openai_client.beta.threads.messages.create(
                            thread_id=thread.id,
                            role=role,
                            content=content,
                        )
                    except Exception as hist_e:
                        # Non-fatal: some API versions reject "assistant" role on create.
                        logger.debug(f"Could not replay history turn (role={role}): {hist_e}")

            # Add the current user query.
            await openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message,
            )

            logger.info(f"Executing run on thread {thread.id} ...")
            run = await openai_client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=agent.id,
                timeout=120,  # 2-minute ceiling for complex multi-search Bing runs
            )

            if run.status != "completed":
                logger.error(
                    f"Run {run.id} ended with status '{run.status}'. "
                    f"last_error={getattr(run, 'last_error', None)}"
                )
                friendly_errors = {
                    "failed":    "The agent encountered an error while researching your query. Please try again.",
                    "expired":   "The search took too long and timed out. Try a more specific question.",
                    "cancelled": "The request was cancelled.",
                }
                msg = friendly_errors.get(run.status, f"Unexpected agent status: {run.status}.")
                return AgentResult(text=msg, usage_metadata={}, sources=[])

            messages_page = await openai_client.beta.threads.messages.list(thread_id=thread.id)
            assistant_messages = [m for m in messages_page.data if m.role == "assistant"]

            if not assistant_messages:
                return AgentResult(text="No response generated from agent.", usage_metadata={}, sources=[])

            final_text, sources = _extract_text_and_citations(assistant_messages[0])

            metadata = {"model": "gpt-4o (Azure AI Agent + Bing Grounding)"}
            if hasattr(run, "usage") and run.usage:
                class _Usage:
                    def __init__(self, r):
                        self.total_tokens = getattr(r.usage, "total_tokens", 0)
                        self.prompt_tokens = getattr(r.usage, "prompt_tokens", 0)
                        self.completion_tokens = getattr(r.usage, "completion_tokens", 0)
                metadata["usage"] = _Usage(run)

            logger.info(f"Run complete. {len(sources)} citation(s) extracted.")
            return AgentResult(text=final_text.strip(), usage_metadata=metadata, sources=sources)

        finally:
            await openai_client.beta.assistants.delete(agent.id)

    except Exception as e:
        logger.error(f"Error in process_chat_message: {e}", exc_info=True)
        return None
