from .command_types import CommandType, UUID_REGEX
from dataclasses import dataclass, field as datafield


@dataclass(frozen=True)
class InfoCommandObject:
    reference_id: str
    _ObjectType: str = datafield(
        default=CommandType.InfoCommand,
        metadata={"valid-values": [CommandType.InfoCommand]},
    )
