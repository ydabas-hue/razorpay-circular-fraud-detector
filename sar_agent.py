import json
import os
import pandas as pd
from openai import OpenAI

_CLIENT = None

def _get_client():
    global _CLIENT
    if _CLIENT is None:
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY environment variable not set.")
        # Added a 30-second timeout to prevent infinite hanging
        _CLIENT = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
            timeout=30.0
        )
    return _CLIENT

def analyze_cycle(cycle_data: dict, entity_registry: pd.DataFrame) -> dict:
    nodes_list = cycle_data["nodes"]
    edges_list = cycle_data["edges"]

    # Build KYC payload for flagged nodes
    nodes_df = entity_registry[entity_registry["entity_id"].isin(nodes_list)]
    kyc_payload = nodes_df.to_dict(orient="records")

    prompt = f"""You are a financial fraud analyst at Razorpay. A graph anomaly detector has flagged a closed {len(nodes_list)}-hop money loop on RazorpayX infrastructure.

Flagged nodes (in order): {nodes_list}

Transactions (Edges):
{json.dumps(edges_list, indent=2)}

Entity KYC metadata:
{json.dumps(kyc_payload, indent=2)}

Analyze whether this is fraudulent round-tripping or a legitimate micro-economy.
Key fraud signals to look for:
- All nodes sharing the same IP subnet (suggests coordinated shell entities)
- MCC codes that are logically unrelated (e.g., software company paying cement supplier)
- All nodes incorporated within a few days of each other (coordinated creation)
- Unusually round or identical transaction amounts across all hops

You MUST respond ONLY with a valid JSON object. Do not include any other text, greetings, or markdown. Use this exact schema:
{{
    "verdict": "FRAUD" or "LEGITIMATE",
    "confidence": 0.95,
    "reasoning": "One paragraph explaining the verdict based on metadata.",
    "sar_summary": "One sentence summary suitable for filing with RBI.",
    "recommended_action": "FREEZE_PAYOUTS", "MONITOR", or "CLEAR"
}}"""

    print("  [LLM AGENT] Sending payload to NVIDIA Llama 3.2 11B (max 30s wait...)")

    response = _get_client().chat.completions.create(
        model="meta/llama-3.2-11b-vision-instruct",
        max_tokens=1000,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the raw text and clean it in case the model hallucinates markdown
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "", 1)
    if content.startswith("```"):
        content = content.replace("```", "", 1)
    if content.endswith("```"):
        content = content[::-1].replace("```", "", 1)[::-1]
        
    return json.loads(content.strip())