#!/usr/bin/env python3
import sys
from orchestrator.human_loop_orchestrator import HumanLoopOrchestrator

def main():
    goal = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("🎯 Sprint hedefini girin: ")
    HumanLoopOrchestrator().run_sprint(goal)

if __name__ == "__main__":
    main()
