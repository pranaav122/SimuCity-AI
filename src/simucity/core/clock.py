"""Discrete simulation clock for SimuCity."""

from pydantic import BaseModel, Field


class SimulationClock(BaseModel):
    """Tracks discrete simulation time across ticks, minutes, hours, and days."""

    current_tick: int = Field(default=0, ge=0, description="Elapsed ticks since simulation start")
    minutes_per_tick: int = Field(default=15, gt=0, description="Simulation minutes per tick")
    start_day: int = Field(default=1, ge=1, description="Starting day index (1-based)")
    start_hour: int = Field(default=8, ge=0, le=23, description="Starting hour (0-23)")
    start_minute: int = Field(default=0, ge=0, le=59, description="Starting minute (0-59)")

    DAYS_OF_WEEK: list[str] = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    @property
    def ticks_per_hour(self) -> int:
        return 60 // self.minutes_per_tick

    @property
    def ticks_per_day(self) -> int:
        return (24 * 60) // self.minutes_per_tick

    @property
    def total_elapsed_minutes(self) -> int:
        return self.current_tick * self.minutes_per_tick

    @property
    def total_minutes_from_origin(self) -> int:
        start_offset = (self.start_hour * 60) + self.start_minute
        return start_offset + self.total_elapsed_minutes

    @property
    def day(self) -> int:
        """Current day (1-based)."""
        return self.start_day + (self.total_minutes_from_origin // (24 * 60))

    @property
    def hour(self) -> int:
        """Current hour of day (0-23)."""
        return (self.total_minutes_from_origin % (24 * 60)) // 60

    @property
    def minute(self) -> int:
        """Current minute of hour (0-59)."""
        return self.total_minutes_from_origin % 60

    @property
    def day_of_week(self) -> str:
        """Day of week string based on day index (Day 1 is Monday)."""
        day_idx = (self.day - 1) % 7
        return self.DAYS_OF_WEEK[day_idx]

    @property
    def is_weekend(self) -> bool:
        return self.day_of_week in ("Saturday", "Sunday")

    @property
    def is_night(self) -> bool:
        """Night time defined as 22:00 to 06:00."""
        return self.hour >= 22 or self.hour < 6

    @property
    def is_class_hours(self) -> bool:
        """Standard campus class hours: Mon-Fri between 08:00 and 17:00."""
        return not self.is_weekend and 8 <= self.hour < 17

    @property
    def is_meal_hours(self) -> bool:
        """Meal times: 08:00-09:30 (Breakfast), 12:00-14:00 (Lunch), 18:00-20:00 (Dinner)."""
        return (8 <= self.hour < 10) or (12 <= self.hour < 14) or (18 <= self.hour < 20)

    @property
    def time_str(self) -> str:
        """Return HH:MM format."""
        return f"{self.hour:02d}:{self.minute:02d}"

    @property
    def formatted(self) -> str:
        """Human-readable full timestamp: Day X (DayOfWeek) HH:MM [Tick N]."""
        return f"Day {self.day} ({self.day_of_week}) {self.time_str} [Tick {self.current_tick}]"

    def advance(self, ticks: int = 1) -> None:
        """Advance the simulation clock by a given number of ticks."""
        if ticks < 0:
            raise ValueError("Ticks to advance must be non-negative.")
        self.current_tick += ticks

    def reset(self) -> None:
        """Reset the clock back to tick 0."""
        self.current_tick = 0
