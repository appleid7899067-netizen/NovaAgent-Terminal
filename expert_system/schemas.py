from pydantic import BaseModel, Field
from typing import List, Optional

class CodeReview(BaseModel):
    has_bugs: bool = Field(description="Does the code have bugs?")
    security_issues: List[str] = Field(description="List of security vulnerabilities found")
    performance_issues: List[str] = Field(description="List of performance bottlenecks")
    refactored_code: str = Field(description="The improved, refactored code")
    reasoning: str = Field(description="Step-by-step reasoning for the changes")

class TacticalDecision(BaseModel):
    selected_skill: str
    reasoning: str
    estimated_damage: int
