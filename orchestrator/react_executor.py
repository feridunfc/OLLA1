from dataclasses import dataclass
from typing import Literal, List, Dict, Any

@dataclass
class ExecutionStep:
    kind: Literal['llm','tool']
    name: str
    params: Dict[str, Any]
    requires_approval: bool = False
    stop_condition: str | None = None

async def run_task(steps: List[ExecutionStep], ctx) -> Dict:
    # TODO: Think -> Act -> Observe döngüsü; metrics & budget guard çağrıları
    return {'ok': True, 'steps': len(steps)}
