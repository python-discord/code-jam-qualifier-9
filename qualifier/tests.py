import random
import unittest
import itertools
from types import MappingProxyType
from typing import Any, Awaitable, Callable, Dict, List
from unittest.mock import AsyncMock

import qualifier
from qualifier import Request


STAFF_IDS = (
    "jmMZkSGVBbCDgKKMMSNPS", "HeLlOWoRlD123", "iKnowThatYouAreReadingThis",
    "PyTHonDIscorDCoDEJam", "iWAShereWRITINGthis"
)
SPECIALITIES = (
    "pasta", "meat", "vegetables", "non-food", "dessert",
)


async def _receive() -> None: ...
async def _send(_: object) -> None: ...


class WarnTypoAccess(dict):
    def __getitem__(self, key):
        if key == "specialty":
            raise RuntimeError(
                "You may be using the wrong spelling for 'speciality'"
                "; The correct key name is 'speciality', not 'specialty'."
            )
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key == "specialty":
            raise RuntimeError(
                "You may be using the wrong spelling for 'speciality'"
                "; The correct key name is 'speciality', not 'specialty'."
            )
        return super().get(key, default)


def create_request(
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[object]] = _receive,
        send: Callable[[object], Awaitable[Any]] = _send
) -> Request:
    """
    Create a request object with the given scope and receive/send functions.
    Raises an error with help message if 'specialty' is accessed.
    """
    return Request(MappingProxyType(WarnTypoAccess(scope)), receive, send)


def wrap_receive_mock(id_: str, mock: AsyncMock) -> Callable[[], Awaitable[object]]:
    async def receive() -> object:
        return await mock(id_)
    return receive


def wrap_send_mock(id_: str, mock: AsyncMock) -> Callable[[object], Awaitable[Any]]:
    async def send(obj: object) -> Any:
        return await mock(id_, obj)
    return send


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

        staff = create_request({"type": "staff.onduty", "id": id_, "speciality": [SPECIALITIES[0]]}, receive, send)

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

        await self.manager(create_request({"type": "staff.offduty", "id": id_}, receive, send))

        self.verify_staff_dict()

        self.assertEqual(self.manager.staff, {}, msg="Staff not removed after going off-duty")

    async def test_multiple_staff_registration(self) -> None:
        staff: List[Request] = []

        for id_, speciality in zip(STAFF_IDS, SPECIALITIES):
            receive, send = AsyncMock(), AsyncMock()

            request = create_request({"type": "staff.onduty", "id": id_, "speciality": [speciality]}, receive, send)
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
        staff = create_request(
            {"type": "staff.onduty", "id": id_, "speciality": [SPECIALITIES[-1]]},
            AsyncMock(return_value=result), AsyncMock()
        )

        await self.manager(staff)

        order = create_request(
            {"type": "order", "speciality": SPECIALITIES[-1]},
            AsyncMock(return_value=complete_order), AsyncMock()
        )
        await self.manager(order)

        order.receive.assert_awaited_once()
        staff.send.assert_awaited_once_with(complete_order)

        staff.receive.assert_awaited_once()
        order.send.assert_awaited_once_with(result)

        await self.manager(create_request({"type": "staff.offduty", "id": id_}))

    async def test_handle_multiple_customers(self) -> None:
        # We cannot *necessarily* assume that there will be an even distribution of orders at
        # this point. We should decouple the testing of orders being delivered to staff, and
        # the testing of the distribution of those orders.

        # List of tuple with the first item being the order and the second
        # being the result.
        sentinels = [(object(), object()) for _ in range(len(STAFF_IDS))]

        # By reusing these we don't need to care about which staff was sent the order.
        staff_receive, staff_send = AsyncMock(), AsyncMock()
        staff = [
            create_request(
                {"type": "staff.onduty", "id": id_, "speciality": [speciality]},

                # We wrap the mocks so that they pass the ID of the staff, that way
                # we can ensure that the order was both sent and received to the same staff.
                wrap_receive_mock(id_, staff_receive), wrap_send_mock(id_, staff_send)
            )
            for id_, speciality in zip(STAFF_IDS, reversed(SPECIALITIES))
        ]

        for request in staff:
            await self.manager(request)

        orders = [
            create_request({"type": "order", "speciality": speciality}, AsyncMock(), AsyncMock())
            for speciality in SPECIALITIES
        ]

        for order, (full_order, result) in zip(orders, sentinels):
            order.receive.return_value = full_order
            staff_receive.return_value = result

            await self.manager(order)

            staff_send.assert_awaited_once()

            # We assert that it is 2 arguments, because the wrapper over the mock passes an additional one
            self.assertEqual(
                len(staff_send.call_args.args), 2,
                msg="Staff send method not awaited with correct amount of arguments"
            )

            staff_id = staff_send.call_args.args[0]
            staff_send.assert_awaited_once_with(staff_id, full_order)

            # Make sure the same staff was also received from
            staff_receive.assert_awaited_once_with(staff_id)

            order.receive.assert_awaited_once_with()
            order.send.assert_awaited_once_with(result)

            staff_receive.reset_mock()
            staff_send.reset_mock()

        for request in staff:
            await self.manager(create_request({"type": "staff.offduty", "id": request.scope["id"]}))

    async def test_order_speciality_match(self) -> None:
        staff_ids, specialities = list(STAFF_IDS), list(SPECIALITIES)
        random.shuffle(staff_ids)
        random.shuffle(specialities)

        staff_receive, staff_send = AsyncMock(), AsyncMock()
        staff = {
            id_: create_request(
                {"type": "staff.onduty", "id": id_, "speciality": [speciality]},

                # We wrap the mocks so that they pass the ID of the staff, that way
                # we can ensure that the order was both sent and received to the same staff.
                wrap_receive_mock(id_, staff_receive), wrap_send_mock(id_, staff_send)
            )
            for id_, speciality in zip(staff_ids, specialities)
        }

        for request in staff.values():
            await self.manager(request)

        orders = [create_request({"type": "order", "speciality": speciality}) for speciality in specialities * 10]

        for order in orders:
            await self.manager(order)

            staff_send.assert_awaited_once()
            staff_id = staff_send.call_args.args[0]

            self.assertIn(
                order.scope["speciality"], staff[staff_id].scope["speciality"],
                msg="Order speciality not matched with speciality of staff"
            )
            staff_send.reset_mock()

        for request in staff.values():
            await self.manager(create_request({"type": "staff.offduty", "id": request.scope["id"]}))

    async def test_uneven_order_speciality(self) -> None:
        # Similar to test_order_speciality_match() but there are multiple staff
        # with the same speciality.
        staff_ids, specialities = list(STAFF_IDS), list(SPECIALITIES[:2])
        random.shuffle(staff_ids)
        random.shuffle(specialities)

        staff_receive, staff_send = AsyncMock(), AsyncMock()
        staff = {
            id_: create_request(
                {"type": "staff.onduty", "id": id_, "speciality": [speciality]},

                # We wrap the mocks so that they pass the ID of the staff, that way
                # we can ensure that the order was both sent and received to the same staff.
                wrap_receive_mock(id_, staff_receive), wrap_send_mock(id_, staff_send)
            )
            for id_, speciality in zip(staff_ids, itertools.cycle(specialities))
        }

        for request in staff.values():
            await self.manager(request)

        orders = [
            create_request({"type": "order", "speciality": speciality})
            for speciality in itertools.chain(*itertools.repeat(specialities, 5))
        ]

        for order in orders:
            await self.manager(order)

            staff_send.assert_awaited_once()
            staff_id = staff_send.call_args.args[0]

            self.assertIn(
                order.scope["speciality"], staff[staff_id].scope["speciality"],
                msg="Order speciality not matched with speciality of staff"
            )
            staff_send.reset_mock()

        for request in staff.values():
            await self.manager(create_request({"type": "staff.offduty", "id": request.scope["id"]}))

    async def test_multiple_specialities(self) -> None:
        id_one, id_two = random.sample(STAFF_IDS, 2)

        staff_receive, staff_send = AsyncMock(), AsyncMock()

        staff_one = create_request(
            {"type": "staff.onduty", "id": id_one, "speciality": [SPECIALITIES[0]]},
            wrap_receive_mock(id_one, staff_receive),
            wrap_send_mock(id_one, staff_send)
        )
        await self.manager(staff_one)

        staff_two = create_request(
            {"type": "staff.onduty", "id": id_two, "speciality": SPECIALITIES[1:]},
            wrap_receive_mock(id_two, staff_receive),
            wrap_send_mock(id_two, staff_send)
        )
        await self.manager(staff_two)

        orders = [
            create_request({"type": "order", "speciality": speciality})
            for speciality in itertools.chain(*itertools.repeat(SPECIALITIES, 5))
        ]

        for order in orders:
            await self.manager(order)

            staff_send.assert_awaited_once()
            staff_id = staff_send.call_args.args[0]
            if order.scope["speciality"] == SPECIALITIES[0]:
                self.assertEqual(staff_id, staff_one.scope["id"], msg="Order speciality not match with speciality of staff")
            else:
                self.assertEqual(staff_id, staff_two.scope["id"], msg="Order speciality not match with speciality of staff")

            staff_send.reset_mock()
