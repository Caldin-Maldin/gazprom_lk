"""Base entity for Gazprom LK."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import DOMAIN
from .coordinator import GazpromLKDataUpdateCoordinator

class GazpromLKEntity(CoordinatorEntity[GazpromLKDataUpdateCoordinator]):
    """Base entity for Gazprom LK."""
    
    _attr_has_entity_name = True

    def __init__(self, coordinator: GazpromLKDataUpdateCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        
        ls_number = coordinator.data.get("ls_number", "") if coordinator.data else ""
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            manufacturer="Газпром Межрегионгаз",
            name=f"Лицевой счет {ls_number}",
            model="Личный кабинет"
        )
