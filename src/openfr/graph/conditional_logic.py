"""
Conditional logic for graph routing.
"""

from openfr.agents.utils.agent_states import AgentState


class ConditionalLogic:
    """处理图的条件路由逻辑"""

    def __init__(self, max_debate_rounds: int = 1, max_risk_discuss_rounds: int = 1):
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_debate(self, state: AgentState) -> str:
        if state["investment_debate_state"]["count"] >= 2 * self.max_debate_rounds:
            return "Research Manager"
        if state["investment_debate_state"]["current_response"].startswith("多头"):
            return "Bear Researcher"
        return "Bull Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        if state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds:
            return "Portfolio Manager"
        latest_speaker = state["risk_debate_state"]["latest_speaker"]
        if latest_speaker == "Aggressive":
            return "Conservative Analyst"
        elif latest_speaker == "Conservative":
            return "Neutral Analyst"
        return "Aggressive Analyst"
