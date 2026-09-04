"""Environment topology and spatial location graph for the university campus."""

from enum import Enum

import networkx as nx
from pydantic import BaseModel, Field


class LocationType(str, Enum):
    DORMITORY = "dormitory"
    CLASSROOM = "classroom"
    LIBRARY = "library"
    CAFETERIA = "cafeteria"
    SHOP = "shop"
    RECREATION = "recreation"
    TRANSPORT = "transport"
    ADMIN = "admin"


class LocationAffordance(str, Enum):
    SLEEP = "sleep"
    REST = "rest"
    STUDY = "study"
    ATTEND_CLASS = "attend_class"
    EAT = "eat"
    PURCHASE = "purchase"
    WORK = "work"
    SOCIALIZE = "socialize"
    EXERCISE = "exercise"
    TRANSIT = "transit"
    ADMIN_TASK = "admin_task"


class Location(BaseModel):
    """A distinct physical location within the simulation environment."""

    id: str = Field(description="Unique location identifier")
    name: str = Field(description="Human-readable location name")
    type: LocationType = Field(description="Categorical type of the location")
    capacity: int = Field(default=50, gt=0, description="Maximum simultaneous agent capacity")
    affordances: set[LocationAffordance] = Field(
        default_factory=set, description="Set of actions enabled at this location"
    )
    base_cost: float = Field(
        default=0.0, ge=0.0, description="Base monetary cost to utilize amenities"
    )
    opening_hour: int = Field(default=0, ge=0, le=23, description="Opening hour in 24h format")
    closing_hour: int = Field(
        default=24, ge=0, le=24, description="Closing hour in 24h format (24=midnight/24h)"
    )
    base_noise_level: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Base environmental noise [0-1]"
    )
    comfort_level: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Rest/comfort factor [0-1]"
    )
    occupants: set[str] = Field(
        default_factory=set, description="Set of agent IDs currently present"
    )

    def is_open(self, current_hour: int) -> bool:
        """Check if facility is open at the given hour."""
        if self.opening_hour == 0 and self.closing_hour == 24:
            return True
        if self.opening_hour < self.closing_hour:
            return self.opening_hour <= current_hour < self.closing_hour
        else:
            # Over-midnight opening (e.g. 18:00 to 02:00)
            return current_hour >= self.opening_hour or current_hour < self.closing_hour

    @property
    def current_occupancy(self) -> int:
        return len(self.occupants)

    @property
    def has_capacity(self) -> bool:
        return len(self.occupants) < self.capacity

    @property
    def available_slots(self) -> int:
        return max(0, self.capacity - len(self.occupants))

    @property
    def crowding_factor(self) -> float:
        """Normalized crowding metric between 0.0 and 1.0+."""
        return len(self.occupants) / float(self.capacity)

    def effective_noise(self) -> float:
        """Calculates dynamic noise level based on current occupancy."""
        crowd_noise = (len(self.occupants) / max(1, self.capacity)) * 0.5
        return min(1.0, self.base_noise_level + crowd_noise)

    def allows(self, affordance: LocationAffordance) -> bool:
        return affordance in self.affordances

    def add_occupant(self, agent_id: str) -> bool:
        """Add agent if not already present. Returns True if successfully added."""
        if len(self.occupants) >= self.capacity and agent_id not in self.occupants:
            return False
        self.occupants.add(agent_id)
        return True

    def remove_occupant(self, agent_id: str) -> None:
        self.occupants.discard(agent_id)


class CampusEnvironment:
    """Manages the network of spatial locations and agent movements."""

    def __init__(self) -> None:
        self.locations: dict[str, Location] = {}
        self._graph: nx.Graph = nx.Graph()

    def add_location(self, location: Location) -> None:
        self.locations[location.id] = location
        self._graph.add_node(location.id, data=location)

    def add_path(self, from_id: str, to_id: str, travel_ticks: int = 1) -> None:
        """Add bidirectional path with travel duration in simulation ticks."""
        if from_id not in self.locations or to_id not in self.locations:
            raise KeyError(f"Both locations {from_id} and {to_id} must exist in environment.")
        self._graph.add_edge(from_id, to_id, weight=max(1, travel_ticks))

    def get_location(self, location_id: str) -> Location:
        if location_id not in self.locations:
            raise KeyError(f"Location '{location_id}' not found in environment.")
        return self.locations[location_id]

    def get_all_locations(self) -> list[Location]:
        return list(self.locations.values())

    def get_travel_ticks(self, origin_id: str, destination_id: str) -> int:
        """Calculate shortest path travel time in ticks between two locations."""
        if origin_id == destination_id:
            return 0
        if origin_id not in self.locations or destination_id not in self.locations:
            raise KeyError(f"Invalid path query between {origin_id} and {destination_id}")
        try:
            length = nx.shortest_path_length(
                self._graph, source=origin_id, target=destination_id, weight="weight"
            )
            return int(length)
        except nx.NetworkXNoPath:
            return 999999  # Unreachable

    def move_agent(self, agent_id: str, from_loc_id: str | None, to_loc_id: str) -> bool:
        """Move agent from one location to another. Validates target capacity."""
        target_loc = self.get_location(to_loc_id)
        if not target_loc.has_capacity and agent_id not in target_loc.occupants:
            return False

        if from_loc_id and from_loc_id in self.locations:
            self.locations[from_loc_id].remove_occupant(agent_id)

        target_loc.add_occupant(agent_id)
        return True

    def remove_agent_from_all(self, agent_id: str) -> None:
        for loc in self.locations.values():
            loc.remove_occupant(agent_id)

    def get_agent_location_id(self, agent_id: str) -> str | None:
        for loc in self.locations.values():
            if agent_id in loc.occupants:
                return loc.id
        return None

    def get_co_located_agents(self, agent_id: str) -> list[str]:
        """Return all other agents in the same location as agent_id."""
        loc_id = self.get_agent_location_id(agent_id)
        if not loc_id:
            return []
        loc = self.get_location(loc_id)
        return [other_id for other_id in loc.occupants if other_id != agent_id]

    @classmethod
    def create_default_campus(cls) -> "CampusEnvironment":
        """Factory method to construct the standard university campus layout."""
        env = cls()

        # 1. Dormitories (24/7, high comfort, sleep/rest/study)
        env.add_location(
            Location(
                id="dorm_north",
                name="North Residential Hall",
                type=LocationType.DORMITORY,
                capacity=120,
                affordances={
                    LocationAffordance.SLEEP,
                    LocationAffordance.REST,
                    LocationAffordance.STUDY,
                    LocationAffordance.SOCIALIZE,
                },
                base_cost=0.0,
                opening_hour=0,
                closing_hour=24,
                base_noise_level=0.2,
                comfort_level=0.9,
            )
        )
        env.add_location(
            Location(
                id="dorm_south",
                name="South Residential Hall",
                type=LocationType.DORMITORY,
                capacity=120,
                affordances={
                    LocationAffordance.SLEEP,
                    LocationAffordance.REST,
                    LocationAffordance.STUDY,
                    LocationAffordance.SOCIALIZE,
                },
                base_cost=0.0,
                opening_hour=0,
                closing_hour=24,
                base_noise_level=0.2,
                comfort_level=0.9,
            )
        )

        # 2. Classrooms (08:00 - 18:00, academic lectures & study)
        env.add_location(
            Location(
                id="classroom_hall",
                name="Academic Lecture Complex",
                type=LocationType.CLASSROOM,
                capacity=150,
                affordances={
                    LocationAffordance.ATTEND_CLASS,
                    LocationAffordance.STUDY,
                    LocationAffordance.SOCIALIZE,
                },
                base_cost=0.0,
                opening_hour=8,
                closing_hour=18,
                base_noise_level=0.4,
                comfort_level=0.5,
            )
        )

        # 3. Library (07:00 - 24:00, high focus, low noise)
        env.add_location(
            Location(
                id="central_library",
                name="Main University Library",
                type=LocationType.LIBRARY,
                capacity=80,
                affordances={
                    LocationAffordance.STUDY,
                    LocationAffordance.REST,
                },
                base_cost=0.0,
                opening_hour=7,
                closing_hour=24,
                base_noise_level=0.05,
                comfort_level=0.8,
            )
        )

        # 4. Cafeteria (07:30 - 21:00, meals, casual socialization)
        env.add_location(
            Location(
                id="dining_hall",
                name="Student Commons Cafeteria",
                type=LocationType.CAFETERIA,
                capacity=100,
                affordances={
                    LocationAffordance.EAT,
                    LocationAffordance.PURCHASE,
                    LocationAffordance.SOCIALIZE,
                    LocationAffordance.WORK,
                },
                base_cost=8.0,  # $8 per standard meal
                opening_hour=7,
                closing_hour=21,
                base_noise_level=0.6,
                comfort_level=0.6,
            )
        )

        # 5. Shops & Convenience (08:00 - 22:00, supplies, coffee, part-time work)
        env.add_location(
            Location(
                id="campus_store",
                name="Campus Mart & Cafe",
                type=LocationType.SHOP,
                capacity=40,
                affordances={
                    LocationAffordance.PURCHASE,
                    LocationAffordance.EAT,
                    LocationAffordance.WORK,
                    LocationAffordance.SOCIALIZE,
                },
                base_cost=4.0,  # $4 quick snack/coffee
                opening_hour=8,
                closing_hour=22,
                base_noise_level=0.4,
                comfort_level=0.5,
            )
        )

        # 6. Recreation Center (06:00 - 22:00, sports, stress reduction)
        env.add_location(
            Location(
                id="rec_center",
                name="Fitness & Recreation Complex",
                type=LocationType.RECREATION,
                capacity=75,
                affordances={
                    LocationAffordance.EXERCISE,
                    LocationAffordance.REST,
                    LocationAffordance.SOCIALIZE,
                },
                base_cost=2.0,
                opening_hour=6,
                closing_hour=22,
                base_noise_level=0.5,
                comfort_level=0.7,
            )
        )

        # 7. Transportation Hub (24/7, shuttle & transit)
        env.add_location(
            Location(
                id="transit_hub",
                name="Central Transit Plaza",
                type=LocationType.TRANSPORT,
                capacity=200,
                affordances={
                    LocationAffordance.TRANSIT,
                    LocationAffordance.SOCIALIZE,
                },
                base_cost=1.5,
                opening_hour=0,
                closing_hour=24,
                base_noise_level=0.5,
                comfort_level=0.3,
            )
        )

        # 8. Administrative Building (08:30 - 17:00, financial, registration, admin)
        env.add_location(
            Location(
                id="admin_center",
                name="Administration & Student Services",
                type=LocationType.ADMIN,
                capacity=50,
                affordances={
                    LocationAffordance.ADMIN_TASK,
                    LocationAffordance.WORK,
                    LocationAffordance.SOCIALIZE,
                },
                base_cost=0.0,
                opening_hour=8,
                closing_hour=17,
                base_noise_level=0.3,
                comfort_level=0.6,
            )
        )

        # Campus Network Topology (edges with realistic travel costs in ticks, 1 tick = 15 min)
        # Transit Hub is centrally connected
        env.add_path("transit_hub", "dorm_north", travel_ticks=1)
        env.add_path("transit_hub", "dorm_south", travel_ticks=1)
        env.add_path("transit_hub", "classroom_hall", travel_ticks=1)
        env.add_path("transit_hub", "dining_hall", travel_ticks=1)
        env.add_path("transit_hub", "central_library", travel_ticks=1)
        env.add_path("transit_hub", "rec_center", travel_ticks=1)
        env.add_path("transit_hub", "campus_store", travel_ticks=1)
        env.add_path("transit_hub", "admin_center", travel_ticks=1)

        # Direct walkways between adjacent facilities
        env.add_path("dorm_north", "dining_hall", travel_ticks=1)
        env.add_path("dorm_north", "campus_store", travel_ticks=1)
        env.add_path("dorm_south", "rec_center", travel_ticks=1)
        env.add_path("dorm_south", "classroom_hall", travel_ticks=1)
        env.add_path("classroom_hall", "central_library", travel_ticks=1)
        env.add_path("classroom_hall", "dining_hall", travel_ticks=1)
        env.add_path("dining_hall", "campus_store", travel_ticks=1)
        env.add_path("admin_center", "classroom_hall", travel_ticks=1)
        env.add_path("admin_center", "central_library", travel_ticks=1)

        return env
