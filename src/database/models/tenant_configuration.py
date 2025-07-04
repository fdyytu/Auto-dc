from dataclasses import dataclass
from datetime import datetime

@dataclass
class TenantConfiguration:
    id: int
    tenant_id: str
    bot_token: str
    donation_channel_id: str
    other_channel_ids: str
    created_at: str
    updated_at: str

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "bot_token": self.bot_token,
            "donation_channel_id": self.donation_channel_id,
            "other_channel_ids": self.other_channel_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
