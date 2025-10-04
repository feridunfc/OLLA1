
import sys
from orchestrator.human_loop_orchestrator import HumanLoopOrchestrator

def main():
    goal = sys.argv[1] if len(sys.argv) > 1 else "FastAPI'ye JWT auth ekle"
    auto = "--auto" in sys.argv
    HumanLoopOrchestrator(auto=auto).run_sprint(goal)

if __name__ == "__main__":
    main()
