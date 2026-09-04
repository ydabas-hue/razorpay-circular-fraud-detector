import json
import os
import re
import pandas as pd
from openai import OpenAI

DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
FALLBACK_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

_CLIENT = None
_INSTRUCTIONS = None


def _load_env():
    """Load key-value pairs from .env if present and not already set in environment."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ and v:
                    os.environ[k] = v


def _load_agent_instructions() -> str:
    """Load system instructions and personality definition from agents/sar_analyst.md."""
    global _INSTRUCTIONS
    if _INSTRUCTIONS is None:
        md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents", "sar_analyst.md")
        if os.path.isfile(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Strip YAML frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            _INSTRUCTIONS = content
        else:
            _INSTRUCTIONS = (
                "You are a Senior AML Forensic Investigator at RazorpayX. "
                "Analyze transaction cycles and KYC metadata to distinguish fraud from legitimate commerce. "
                "Return only valid JSON."
            )
    return _INSTRUCTIONS


def _get_client():
    global _CLIENT
    if _CLIENT is None:
        _load_env()
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY environment variable not set. Add it to .env or export it.")
        _CLIENT = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
            timeout=60.0,
        )
    return _CLIENT


def _extract_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0), strict=False)
        raise


def _invoke_model(client: OpenAI, model: str, system_prompt: str, user_prompt: str) -> dict:
    response = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
    return _extract_json(content)


def analyze_cycle(cycle_data: dict, entity_registry: pd.DataFrame) -> dict:
    nodes_list = cycle_data["nodes"]
    edges_list = cycle_data["edges"]

    # Build KYC payload for flagged nodes
    nodes_df = entity_registry[entity_registry["entity_id"].isin(nodes_list)]
    kyc_payload = nodes_df.to_dict(orient="records")

    system_prompt = _load_agent_instructions()

    user_prompt = f"""Investigate the following flagged closed {len(nodes_list)}-hop transaction cycle:

Flagged Nodes: {nodes_list}

Transactions (Edges):
{json.dumps(edges_list, indent=2)}

Entity KYC Metadata:
{json.dumps(kyc_payload, indent=2)}

Evaluate whether this cycle represents coordinated circular round-tripping or legitimate supply-chain commerce.
Return your findings strictly in the required JSON schema."""

    client = _get_client()
    default_model = os.environ.get("NVIDIA_MODEL", DEFAULT_MODEL)
    fallback_model = os.environ.get("NVIDIA_FALLBACK_MODEL", FALLBACK_MODEL)

    print(f"  [LLM AGENT] Querying primary model: {default_model}...")
    try:
        return _invoke_model(client, default_model, system_prompt, user_prompt)
    except Exception as err:
        print(f"  [LLM AGENT] Primary model ({default_model}) failed: {err}. Retrying with fallback model: {fallback_model}...")
        return _invoke_model(client, fallback_model, system_prompt, user_prompt)