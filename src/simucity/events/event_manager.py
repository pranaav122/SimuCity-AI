"""Event manager handling event lifecycles, active state changes, and engine hooks."""

from typing import Dict, List
from simucity.core.engine import SimulationEngine
from simucity.events.event import SimulationEvent


class EventManager:
    """Schedules, activates, and cleans up dynamic simulation events."""

    def __init__(self) -> None:
        self.events: Dict[str, SimulationEvent] = {}

    def schedule_event(self, event: SimulationEvent) -> None:
        self.events[event.id] = event

    def tick(self, current_tick: int, engine: SimulationEngine) -> List[SimulationEvent]:
        """Evaluates all events, applies modifiers to the engine, and returns newly triggered events."""
        just_activated = []

        for event in self.events.values():
            was_active = event.is_active
            is_active_now = event.is_triggered(current_tick)
            event.is_active = is_active_now

            if is_active_now and not was_active:
                # Newly triggered
                just_activated.append(event)
                engine.add_event(event.id)
                # Apply price multipliers
                for loc_id, mult in event.price_multipliers.items():
                    engine.set_price_multiplier(loc_id, mult)

            elif not is_active_now and was_active:
                # Expired event cleanup
                engine.remove_event(event.id)
                for loc_id in event.price_multipliers.keys():
                    engine.set_price_multiplier(loc_id, 1.0)

        return just_activated
