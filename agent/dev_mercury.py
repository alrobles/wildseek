"""Dev tooling — non-Muse providers (Inception Mercury).

INTERNAL ONLY: never shipped in the public snapshot (release.exclude)
and never part of the product pipeline — product decisions are
recorded by Muse models (hackathon rule). 100M free tokens for
boilerplate-speed dev work + cheap typed decisions for QC tests.

    from agent.dev_mercury import MercuryClient
    c = MercuryClient()          # INCEPTION_API_KEY from
                                 # ~/env/inception-mercury-key
    c.decide(state, questions)   # typed noul/choice/score/extract
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from meta_client import MetaClient, Usage  # noqa: E402

INC_BASE_URL = "https://api.inceptionlabs.ai/v1"
MODEL_INC_JUDGE = "mercury-3"       # 1M ctx, reasoning_effort param
MODEL_INC_FAST = "mercury-2.5"      # prev gen, 260K ctx
INC_PRICES = {                      # 50%-off launch prices
    MODEL_INC_JUDGE: (0.01, 0.10, 0.35),
    MODEL_INC_FAST: (0.02, 0.20, 0.75),
    "mercury-decide": (0.0, 0.02, 0.0),   # input-only billing
}


class MercuryClient(MetaClient):
    def __init__(self):
        super().__init__(api_key=os.environ["INCEPTION_API_KEY"],
                         base_url=INC_BASE_URL)

    def decide(self, state, questions: dict, retries: int = 3) -> dict:
        """Typed decisions over shared state (internal QC testing).
        questions: {name: {type: noul|choice|score|extract, ...}}.
        Returns {answers, usage, cost_usd}."""
        body = {"model": "mercury-decide", "state": state,
                "questions": questions}
        for attempt in range(retries):
            r = self._http.post(f"{self.base}/decisions", json=body,
                                timeout=60)
            if r.status_code == 429 and attempt < retries - 1:
                time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
                continue
            r.raise_for_status()
            break
        data = r.json()
        usage = Usage(prompt_tokens=(data.get("usage") or {})
                      .get("input_tokens", 0),
                      completion_tokens=(data.get("usage") or {})
                      .get("output_tokens", 0))
        pin, pout = 0.02, 0.0
        cost = (usage.prompt_tokens * pin +
                usage.completion_tokens * pout) / 1e6
        self.spend.add("mercury-decide", cost)
        return {"answers": data.get("answers", {}), "usage": usage,
                "cost_usd": cost}
