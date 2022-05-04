import unittest
from types import MappingProxyType
from typing import Any, Awaitable, Callable
from unittest.mock import AsyncMock

import qualifier
from boilerplate import Request


async def _receive() -> None: ...
async def _send(_: object) -> None: ...


def create_request(
        scope: dict[str, str],
        receive: Callable[[], Awaitable[object]] = _receive,
        send: Callable[[object], Awaitable[Any]] = _send
) -> Request:
    return Request(MappingProxyType(scope), receive, send)


class OnDutyTests(unittest.IsolatedAsyncioTestCase):
    """Test that the qualifier implemented Step 1 correctly."""

    def setUp(self):
        self.manager = qualifier.RestaurantManager()

    def test_manager_staff_dict(self):
        self.assertTrue(hasattr(self.manager, "staff"), msg="Restaurant manager has no staff attribute")

        # This is safe against different hooks that isinstance() has
        self.assertIs(type(self.manager.staff), dict, msg="'staff' attribute is not a dictionary")

    async def test_staff_registration(self):
        receive, send = AsyncMock(), AsyncMock()

        staff = create_request({"type": "staff.onduty", "id": "jmMZkSGVBbCDgKKMMSNPS"}, receive, send)

        await self.manager(staff)

        self.test_manager_staff_dict()  # Manager may have overriden it after adding staff

        # These are separated to be more helpful when failing
        self.assertEqual(len(self.manager.staff), 1, msg="Not the correct amount of staff registered")
        self.assertIn("jmMZkSGVBbCDgKKMMSNPS", self.manager.staff, msg="Staff not registered with the correct ID")
        self.assertEqual(
            self.manager.staff["jmMZkSGVBbCDgKKMMSNPS"], staff,
            msg="Staff request not stored as dictionary value"
        )
