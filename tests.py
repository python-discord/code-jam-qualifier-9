import unittest
import unittest.mock
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


STAFF_IDS = (
    "jmMZkSGVBbCDgKKMMSNPS", "HeLlOWoRlD123", "iKnowThatYouAreReadingThis",
    "PyTHonDIscorDCoDEJam", "iWAShereWRITINGthis"
)


class QualifierTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.manager = qualifier.RestaurantManager()

    def verify_staff_dict(self):
        self.assertTrue(hasattr(self.manager, "staff"), msg="Restaurant manager has no staff attribute")
        staff = self.manager.staff

        # This is safe against different hooks that isinstance() has
        self.assertIs(type(staff), dict, msg="'staff' attribute is not a dictionary")
        for key, value in staff.items():
            self.assertIs(type(key), str, msg="Staff dictionary key is not a string")
            self.assertIs(type(value), Request, msg="Staff dictionary value is not a Request")


class RegistrationTests(QualifierTestCase):
    """Test that the qualifier implemented Step 1 correctly."""

    def test_manager_staff_dict(self):
        self.verify_staff_dict()

    async def test_staff_registration(self):
        id_ = STAFF_IDS[0]
        receive, send = AsyncMock(), AsyncMock()

        staff = create_request({"type": "staff.onduty", "id": id_}, receive, send)

        await self.manager(staff)

        self.verify_staff_dict()  # Manager may have overriden it after adding staff

        # These are separated to be more helpful when failing
        self.assertEqual(len(self.manager.staff), 1, msg="Not the correct amount of staff registered")
        self.assertIn(id_, self.manager.staff, msg="Staff not registered with the correct ID")
        self.assertEqual(
            self.manager.staff[id_], staff,
            msg="Staff request not stored as dictionary value"
        )

        receive.assert_not_called()
        send.assert_not_called()

        receive.reset_mock()
        send.reset_mock()

        await self.manager(create_request({"type": "staff.offduty", "id": "jmMZkSGVBbCDgKKMMSNPS"}, receive, send))

        self.verify_staff_dict()

        self.assertEqual(self.manager.staff, {}, msg="Staff not removed after going off-duty")

    async def test_multiple_staff_registration(self) -> None:
        staff: list[Request] = []

        for id_ in STAFF_IDS:
            receive, send = AsyncMock(), AsyncMock()

            request = create_request({"type": "staff.onduty", "id": id_}, receive, send)
            staff.append(request)

            await self.manager(request)

        self.verify_staff_dict()  # Ensure it is still a dictionary for the following assertions

        self.assertEqual(len(self.manager.staff), len(STAFF_IDS), msg="Not all staff were registered")

        for id_, request in zip(STAFF_IDS, staff):
            with self.subTest(staff_id=id_):
                self.assertIn(id_, self.manager.staff, msg="Registered staff's ID not found in dictionary")
                self.assertEqual(self.manager.staff[id_], request, msg="Staff request not stored as dictionary value")

                request.receive.assert_not_called()
                request.send.assert_not_called()

        for id_, request in zip(STAFF_IDS, staff):
            with self.subTest(staff_id=id_):

                request.receive.reset_mock()
                request.send.reset_mock()

                await self.manager(create_request({"type": "staff.offduty", "id": id_}, request.receive, request.send))

        self.verify_staff_dict()
        self.assertEqual(self.manager.staff, {}, msg="Not all staff removed after going off-duty")


class DeliveringTests(QualifierTestCase):

    async def test_handle_customer(self) -> None:
        id_ = STAFF_IDS[-1]

        complete_order, result = object(), object()
        staff = create_request({"type": "staff.onduty", "id": id_}, AsyncMock(return_value=result), AsyncMock())

        await self.manager(staff)

        order = create_request({"type": "order"}, AsyncMock(return_value=complete_order), AsyncMock())
        await self.manager(order)

        order.receive.assert_called_once()
        staff.send.assert_called_once_with(complete_order)

        staff.receive.assert_called_once()
        order.send.assert_called_once_with(result)

        await self.manager(create_request({"type": "staff.offduty", "id": id_}))

    async def test_handle_multipler_customers(self) -> None:
        # We cannot *necessarily* assume that there will be an even distribution of orders at
        # this point. We should decouple the testing of orders being delivered to staff, and
        # the testing of the distribution of those orders.

        # List of tuple with the first item being the order and the second
        # being the result.
        sentinels = [(object(), object()) for _ in range(len(STAFF_IDS))]

        # By reusing these we don't need to care about which
        staff_receive, staff_send = AsyncMock(), AsyncMock()
        staff = {
            create_request({"type": "staff.onduty", "id": id_}, staff_receive, staff_send): sentinel
            for id_, sentinel in zip(STAFF_IDS, sentinels)
        }

        orders = [create_request({"type": "order"}, AsyncMock(), AsyncMock()) for _ in range(len(STAFF_IDS))]

        # TODO: Verify that the order was delivered to a staff
