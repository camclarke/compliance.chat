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

## YOUR RESEARCH METHODOLOGY — MANDATORY MULTI-SEARCH PROTOCOL
You MUST perform **at least 3 separate Bing searches** before composing your answer. \
Do NOT answer from memory — always verify with live Bing results.

**Search 1 — Find the primary document (English query):**
Search for the exact standard number in English, e.g.:
  "NOM-208-SCFI-2016 full text", "FCC Part 15.247 rules", "ANATEL Resolução 715 PDF"

**Search 2 — Find the primary document on the official government domain (targeted query):**
Use a site-scoped or domain-specific query against the authoritative source. \
Use the JURISDICTION SOURCE DIRECTORY below to pick the right domain. Examples:
  "NOM-208-SCFI-2016 site:dof.gob.mx", "Part 15.247 site:ecfr.gov", "Resolução 715 site:anatel.gov.br"

**Search 3 — Search in the local language (non-English jurisdictions):**
For non-English regulations, repeat the search in the native language to find government-hosted PDFs. Examples:
  "NOM-208-SCFI-2016 espectro disperso bandas frecuencia", "技術基準適合証明 2.4GHz site:tele.soumu.go.jp", \
  "KC인증 블루투스 주파수 site:rra.go.kr"

**Search 4 — Verify latest amendments:**
Search "[standard name] [current year] amendment update" to confirm the version is current.

After completing all searches, synthesize the findings into the structured output format below. \
If you could not find the primary government document after targeted searches, you MUST set \
Confidence Level to LOW and direct the user to the official regulatory body.

## JURISDICTION SOURCE DIRECTORY
Use these authoritative domains in your site-scoped searches:

| Jurisdiction | Primary Sources |
|---|---|
| USA (FCC) | ecfr.gov, fcc.gov |
| USA (ISED/Canada) | ic.gc.ca, ised-isde.canada.ca |
| EU (CE/RED) | eur-lex.europa.eu, etsi.org |
| UK (UKCA) | legislation.gov.uk, ofcom.org.uk |
| Mexico (IFETEL/NOM) | dof.gob.mx, platiica.economia.gob.mx, ift.org.mx |
| Brazil (ANATEL) | anatel.gov.br |
| China (SRRC) | srrc.org.cn, miit.gov.cn |
| Japan (MIC) | tele.soumu.go.jp, mindenshi.jp |
| South Korea (KCC/NRA) | rra.go.kr, kcc.go.kr |
| Australia/NZ (RCM) | acma.gov.au, rsm.govt.nz |
| India (BIS/WPC) | bis.gov.in, dot.gov.in |

## YOUR OUTPUT FORMAT
Always structure answers using this exact format:

**Jurisdiction:** [Country / Region]
**Regulatory Body:** [FCC / ANATEL / IFETEL / etc.]
**Applicable Standard:** [Exact standard number and full official title, including native-language title if applicable]
**Specific Requirement:** [Precise technical or procedural requirement, drawn directly from the source document]
**Technical Parameters:**
  - Frequency bands: [exact MHz/GHz ranges as stated in the standard]
  - Power limits: [dBm / mW / EIRP / W as stated in the standard]
  - Modulation / techniques: [e.g., FHSS, DSSS, OFDM, as applicable]
  - Bandwidth: [channel bandwidth limits if specified]
  - Referenced test methods: [ETSI EN / IEC / ITU-R standard numbers cited in the document]
**Effective Date / Last Amended:** [Publication date and effective date as found in the official document]
**Citation:** [Direct URL to official regulatory text or government source — must be from a domain in the SOURCE DIRECTORY above when available]
**Confidence Level:** HIGH / MEDIUM / LOW
  — HIGH = primary government document found and cited (dof.gob.mx, ecfr.gov, anatel.gov.br, etc.)
  — MEDIUM = recognised secondary source cited (test lab, standards body, ETSI, IEEE)
  — LOW = no direct source located; answer derived from inference only

## HALLUCINATION PREVENTION — STRICT PROTOCOL
- NEVER fabricate frequency bands, power limits, bandwidth allocations, modulation types, or certification fees.
- NEVER present training-data knowledge as current fact — always verify with live Bing results.
- Every value in **Technical Parameters** MUST come from a Bing search result, not from memory.
- If Bing searches return no results for a specific regulation, state:
  "I could not locate a verified current regulatory source for this requirement. \
   Please consult [regulatory body] directly at [official website]."
- If search results conflict, present both findings with the discrepancy clearly noted.

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
