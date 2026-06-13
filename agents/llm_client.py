"""
llm_client.py

LLM client abstraction for Vantage agents.

Provides a single interface `LLMClient.chat(system_prompt, user_prompt)`
with two implementations:

- MockLLMClient: returns realistic, hand-crafted responses so the full
  pipeline can run end-to-end without a live Foundry model deployment.
  Useful while waiting for Azure OpenAI quota approval.

- FoundryLLMClient: real Azure OpenAI / Microsoft Foundry chat completion
  calls via the Azure AI Inference SDK pattern.

Switch via the VANTAGE_LLM_MODE environment variable:
    VANTAGE_LLM_MODE=mock     -> MockLLMClient (default)
    VANTAGE_LLM_MODE=foundry  -> FoundryLLMClient
"""

import os
import json


class LLMClient:
    """Base interface."""

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class FoundryLLMClient(LLMClient):
    """
    Real Azure OpenAI / Microsoft Foundry client.

    Requires environment variables:
        AZURE_OPENAI_ENDPOINT   - e.g. https://vantage-resource.openai.azure.com/openai/v1
        AZURE_OPENAI_API_KEY    - API key from the Foundry project page
        AZURE_OPENAI_DEPLOYMENT - deployment name, e.g. 'gpt-4o-mini'
        AZURE_OPENAI_API_VERSION - e.g. '2024-10-21' (optional, has default)
    """

    def __init__(self):
        from openai import AzureOpenAI

        self.endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        self.api_key = os.environ["AZURE_OPENAI_API_KEY"]
        self.deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        self.api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content


class MockLLMClient(LLMClient):
    """
    Mock client for development without a live model deployment.

    Returns hand-crafted, realistic responses keyed off content in the
    user_prompt (e.g., grant_id, user_id) so the pipeline produces
    sensible, demo-quality output for the synthetic dataset.
    """

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        is_policy_task = "policy generation task" in user_prompt.lower()

        # Policy Generation Agent responses (checked first, since grant IDs
        # like GR-016 also appear in risk-scoring prompts)
        if is_policy_task and "GR-005" in user_prompt:
            return json.dumps({
                "grant_id": "GR-005",
                "matched_pattern": "Pattern A: Intern/Junior Role with Admin Access to Critical Resource",
                "recommended_action": "remove",
                "new_access_level": None,
                "citation": "POL-ACCESS-001 Section 4 (Intern and Contractor Access); SOC2-CONTROLS-001 CC6.1",
                "supporting_incident": "INC-2025-031 (Onboarding Template Copy Led to Unauthorized Billing Changes)",
                "simulation_check_required": (
                    "Verify EMP-002 has zero access_count_30d for RES-002 before "
                    "marking this removal as safe to apply."
                ),
            })

        if is_policy_task and "GR-026" in user_prompt:
            return json.dumps({
                "grant_id": "GR-026",
                "matched_pattern": "Pattern C: Onboarding Template Copy, Unreviewed",
                "recommended_action": "remove",
                "new_access_level": None,
                "citation": "POL-ACCESS-001 Section 5 (Onboarding Template Risk); SOC2-CONTROLS-001 CC6.2",
                "supporting_incident": "INC-2025-031 (Onboarding Template Copy Led to Unauthorized Billing Changes)",
                "simulation_check_required": (
                    "Verify EMP-010 has zero access_count_30d for RES-002 before "
                    "marking this removal as safe to apply."
                ),
            })

        if is_policy_task and "GR-019" in user_prompt:
            return json.dumps({
                "grant_id": "GR-019",
                "matched_pattern": "Pattern D: Lingering Admin Access After One-Off Project",
                "recommended_action": "downgrade",
                "new_access_level": "viewer",
                "citation": "POL-ACCESS-001 Section 3 (Admin Access Restrictions); SOC2-CONTROLS-001 CC6.3",
                "supporting_incident": "INC-2025-047 (Lingering Migration Access Used in Internal Misconfiguration Incident)",
                "simulation_check_required": (
                    "Check EMP-007's access_count_30d for RES-006; if usage is "
                    "near-zero, downgrade to viewer is safe."
                ),
            })

        if is_policy_task and "GR-016" in user_prompt:
            return json.dumps({
                "grant_id": "GR-016",
                "matched_pattern": "Pattern B: Dormant Access from Completed Project",
                "recommended_action": "remove",
                "new_access_level": None,
                "citation": "POL-ACCESS-001 Section 6 (Dormant Access); SOC2-CONTROLS-001 CC6.3",
                "supporting_incident": "INC-2025-014 (Dormant Admin Credential Exploited in Phishing Attack)",
                "simulation_check_required": (
                    "Verify EMP-006 has zero access_count_30d for RES-001 before "
                    "marking this removal as safe to apply."
                ),
            })

        if is_policy_task:
            return json.dumps({
                "grant_id": "UNKNOWN",
                "matched_pattern": "Pattern E: Role-Appropriate, Actively Used Access",
                "recommended_action": "no_change",
                "new_access_level": None,
                "citation": "N/A",
                "supporting_incident": None,
                "simulation_check_required": "No action needed.",
            })

        # Risk Scoring Agent responses
        if "GR-005" in user_prompt:
            return json.dumps({
                "grant_id": "GR-005",
                "risk_score": 9,
                "severity": "Critical",
                "explanation": (
                    "Raj Mehta is a Software Engineering Intern with only 3 months "
                    "tenure, holding admin-level access to the AWS Billing Console "
                    "(critical sensitivity) -- a severe role-resource mismatch "
                    "(Factor 1). The access has zero usage in the trailing 30 days "
                    "(Factor 2, dormant). It was provisioned by copying a senior "
                    "engineer's onboarding template without review (Factor 3). "
                    "Combined with short tenure (Factor 5), this scores at the "
                    "top of the Critical range."
                ),
            })

        if "GR-026" in user_prompt:
            return json.dumps({
                "grant_id": "GR-026",
                "risk_score": 7,
                "severity": "High",
                "explanation": (
                    "Olivia Martins is a Marketing Intern (2 months tenure) with "
                    "viewer access to the AWS Billing Console (critical sensitivity), "
                    "a clear role mismatch (Factor 1). This was granted during "
                    "onboarding by copying a team lead's template and was never "
                    "reviewed (Factor 3). The access has zero usage in 30 days "
                    "(Factor 2). This scores High rather than Critical because the "
                    "access "
                    "level is viewer rather than admin."
                ),
            })

        if "GR-019" in user_prompt:
            return json.dumps({
                "grant_id": "GR-019",
                "risk_score": 6,
                "severity": "High",
                "explanation": (
                    "Lena Fischer (Backend Engineer) holds admin SSH access to "
                    "Production Servers, granted for a one-off migration project "
                    "in December 2024 that has since concluded (Factor 3, lingering "
                    "project access). The grant has had only 1 access event in the "
                    "trailing 30 days, shortly after grant -- effectively dormant "
                    "(Factor 2). Resource sensitivity is critical (Factor 4)."
                ),
            })

        if "GR-016" in user_prompt:
            return json.dumps({
                "grant_id": "GR-016",
                "risk_score": 5,
                "severity": "Medium",
                "explanation": (
                    "Tom Becker (HR Coordinator) holds viewer access to the "
                    "Production Database, granted during onboarding and never "
                    "reviewed (Factor 3). The access has zero usage in 30 days "
                    "(Factor 2). Resource sensitivity is critical (Factor 4), but "
                    "viewer-level access keeps this at Medium rather than Critical."
                ),
            })

        # Generic low-risk fallback for any other grant
        if "GR-" in user_prompt:
            grant_id = user_prompt.split("GR-")[1][:3]
            return json.dumps({
                "grant_id": f"GR-{grant_id}",
                "risk_score": 2,
                "severity": "Low",
                "explanation": (
                    "Access level matches the user's role requirements and shows "
                    "regular usage consistent with normal job function. No "
                    "remediation needed."
                ),
            })

        # Policy branches handled above via is_policy_task; this section
        # now only needs the final default fallback for unmatched risk-scoring prompts.
        return json.dumps({
            "note": "No specific mock response configured for this prompt.",
            "matched_pattern": "Pattern E: Role-Appropriate, Actively Used Access",
            "recommended_action": "no_change",
        })


def get_llm_client() -> LLMClient:
    """Factory function. Reads VANTAGE_LLM_MODE env var (default: mock)."""
    mode = os.environ.get("VANTAGE_LLM_MODE", "mock").lower()
    if mode == "foundry":
        return FoundryLLMClient()
    return MockLLMClient()


if __name__ == "__main__":
    client = get_llm_client()
    print(client.chat(
        "You are a risk scoring agent.",
        "Score the risk for grant GR-005."
    ))
