import random
import string
from datetime import datetime

def _activity_id() -> str:
    h = string.hexdigits[:16]
    return '-'.join(''.join(random.choices(h, k=n)) for n in [8, 4, 4, 4, 12])


def log_request(api: str, provider: str, model: str, tokens: int = 0) -> str:
    ts = datetime.now().isoformat()
    tkns = tokens if tokens > 0 else random.randint(100, 500)
    return (
        f'time={ts} level=INFO module=wso2/ai_gateway '
        f'message="AI API request processed" '
        f'activityId="{_activity_id()}" api="{api}" provider="{provider}" '
        f'model="{model}" tokens={tkns} status=200'
    )


def log_guardrail_block(guardrail: str, reason: str, score: float = 1.0,
                        direction: str = "REQUEST") -> str:
    ts = datetime.now().isoformat()
    return (
        f'time={ts} level=WARN module=wso2/ai_gateway '
        f'message="GUARDRAIL_INTERVENED" '
        f'activityId="{_activity_id()}" '
        f'guardrail="{guardrail}" action="GUARDRAIL_INTERVENED" '
        f'actionReason="{reason}" score={score} direction="{direction}" status=446'
    )


def log_system(message: str) -> str:
    ts = datetime.now().isoformat()
    return f'time={ts} level=INFO module=wso2/ai_gateway message="{message}"'
