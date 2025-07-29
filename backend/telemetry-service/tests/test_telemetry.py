import pytest
from pydantic import BaseModel, Field, ValidationError

# Define the models we're testing directly
class TelemetryData(BaseModel):
    device_id: str 
    energy_usage: float

class ScheduleBlock(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_hour: int = Field(..., ge=0, le=23)
    end_hour: int = Field(..., ge=0, le=23)
    power_consumption: float = Field(..., gt=0)

class TestScheduleBlock:
    def test_valid_schedule_block(self):
        """Valid schedule block should be created successfully"""
        schedule = ScheduleBlock(
            day_of_week=1,
            start_hour=9,
            end_hour=17,
            power_consumption=1.5
        )
        
        assert schedule.day_of_week == 1
        assert schedule.start_hour == 9
        assert schedule.end_hour == 17
        assert schedule.power_consumption == 1.5
    
    def test_invalid_day_of_week_high(self):
        """Day of week above 6 should raise validation error"""
        with pytest.raises(ValidationError):
            ScheduleBlock(
                day_of_week=7,  # Should be 0-6
                start_hour=9,
                end_hour=17,
                power_consumption=1.5
            )
    
    def test_invalid_day_of_week_negative(self):
        """Negative day of week should raise validation error"""
        with pytest.raises(ValidationError):
            ScheduleBlock(
                day_of_week=-1,
                start_hour=9,
                end_hour=17,
                power_consumption=1.5
            )
    
    def test_boundary_values(self):
        """Test boundary values for day and hour fields"""
        # Test minimum valid values
        schedule = ScheduleBlock(
            day_of_week=0,
            start_hour=0,
            end_hour=0,
            power_consumption=0.1
        )
        assert schedule.day_of_week == 0
        assert schedule.start_hour == 0
        
        # Test maximum valid values
        schedule = ScheduleBlock(
            day_of_week=6,
            start_hour=23,
            end_hour=23,
            power_consumption=100.0
        )
        assert schedule.day_of_week == 6
        assert schedule.start_hour == 23
    
    def test_invalid_start_hour(self):
        """Start hour above 23 should raise validation error"""
        with pytest.raises(ValidationError):
            ScheduleBlock(
                day_of_week=1,
                start_hour=25,  # Should be 0-23
                end_hour=17,
                power_consumption=1.5
            )
    
    def test_invalid_end_hour(self):
        """End hour above 23 should raise validation error"""
        with pytest.raises(ValidationError):
            ScheduleBlock(
                day_of_week=1,
                start_hour=9,
                end_hour=24,  # Should be 0-23
                power_consumption=1.5
            )
    
    def test_zero_power_consumption(self):
        """Zero power consumption should raise validation error"""
        with pytest.raises(ValidationError):
            ScheduleBlock(
                day_of_week=1,
                start_hour=9,
                end_hour=17,
                power_consumption=0  # Should be > 0
            )
    
    def test_negative_power_consumption(self):
        """Negative power consumption should raise validation error"""
        with pytest.raises(ValidationError):
            ScheduleBlock(
                day_of_week=1,
                start_hour=9,
                end_hour=17,
                power_consumption=-1.0
            )

class TestTelemetryData:
    def test_valid_telemetry_data(self):
        """Valid telemetry data should be created successfully"""
        data = TelemetryData(
            device_id="123e4567-e89b-12d3-a456-426614174000",
            energy_usage=2.5
        )
        
        assert data.device_id == "123e4567-e89b-12d3-a456-426614174000"
        assert data.energy_usage == 2.5
    
    def test_zero_energy_usage(self):
        """Zero energy usage should be allowed"""
        data = TelemetryData(
            device_id="test-device-id",
            energy_usage=0.0
        )
        
        assert data.energy_usage == 0.0
    
    def test_negative_energy_usage(self):
        """Negative energy usage should be allowed for some use cases"""
        data = TelemetryData(
            device_id="test-device-id",
            energy_usage=-1.0
        )
        
        assert data.energy_usage == -1.0
    
    def test_empty_device_id(self):
        """Empty device ID should be allowed by Pydantic (validation can be added later)"""
        data = TelemetryData(
            device_id="",
            energy_usage=1.0
        )
        
        assert data.device_id == ""
    
    def test_large_energy_values(self):
        """Should handle large energy usage values"""
        data = TelemetryData(
            device_id="high-power-device",
            energy_usage=999999.99
        )
        
        assert data.energy_usage == 999999.99
    
    def test_float_precision(self):
        """Should handle precise float values"""
        precise_value = 123.456789
        data = TelemetryData(
            device_id="precise-device",
            energy_usage=precise_value
        )
        
        assert data.energy_usage == precise_value
