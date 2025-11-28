from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator


DriverType = Literal["cli:claude", "api:openai", "cli", "api"]
TrackerType = Literal["jira", "github", "none", "noop"]
StrategyType = Literal["single", "competitive"]

class Profile(BaseModel):
    name: str
    driver: DriverType
    tracker: TrackerType = "none"
    strategy: StrategyType = "single"
    plan_output_dir: str = "docs/plans"

    @model_validator(mode="after")
    def validate_work_profile_constraints(self) -> "Profile":
        """Enterprise constraint: 'work' profiles cannot use API drivers."""
        if self.name.lower() == "work" and self.driver.startswith("api"):
            raise ValueError(f"Profile 'work' cannot use API drivers (got '{self.driver}'). Use CLI drivers for enterprise compliance.")
        return self

class Settings(BaseModel):
    active_profile: str
    profiles: dict[str, Profile]

class Issue(BaseModel):
    id: str
    title: str
    description: str
    status: str = "open"


class Design(BaseModel):
    """Structured design from brainstorming output."""
    title: str
    goal: str
    architecture: str
    tech_stack: list[str]
    components: list[str]
    data_flow: str | None = None
    error_handling: str | None = None
    testing_strategy: str | None = None
    relevant_files: list[str] = Field(default_factory=list)
    conventions: str | None = None
    raw_content: str
