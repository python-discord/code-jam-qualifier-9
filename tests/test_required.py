from unittest.mock import AsyncMock

from framework import Request
from qualifier import RestaurantManager

from ._helpers import step


@step(1)
async def test_register_staff():
    """Test that staff are registered to the dictionary"""
    restaurant = RestaurantManager()
    staff = Request({'type': 'staff.onduty', 'id': 'aBcDeFG'}, AsyncMock(), AsyncMock())

    await restaurant(staff)
    assert staff.scope['id'] in restaurant.staff, "Staff's ID was not present in the dictionary after registration"
    assert restaurant.staff[staff.scope['id']] == staff, "The value of the registered staff's ID wasn't the request"


@step(2, optional=True)
async def test_all_staff_offduty():
    """Test that staff are removed after going off-duty"""
    restaurant = RestaurantManager()
    staff = Request({'type': 'staff.onduty', 'id': 'aBcDeFG'}, AsyncMock(), AsyncMock())

    await restaurant(staff)
    await restaurant(Request({'type': 'staff.offduty', 'id': 'aBcDeFG'}, AsyncMock(), AsyncMock()))

    assert not restaurant.staff, 'Registered restaurant staff is not empty after all staff has gone off-duty'
