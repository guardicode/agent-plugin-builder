from monkeytypes import InfectionMonkeyBaseModel
from pydantic import Field


class PluginOptions(InfectionMonkeyBaseModel):
    agent_binary_download_timeout: float = Field(
        gt=0.0,
        default=60.0,
        title="Agent Binary Download Timeout",
        description="The maximum time (in seconds) to wait for a successfully exploit",
    )
