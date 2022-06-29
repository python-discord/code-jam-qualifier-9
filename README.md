# Summer Code Jam 2022: Qualifier

To qualify for the upcoming Summer Code Jam, you'll have to complete a qualifier assignment. The goal is to make sure you have enough Python knowledge to effectively contribute to a team.

Please read the rules and instructions carefully, and submit your solution before the deadline using the [sign-up form](https://forms.pythondiscord.com/form/cj9-qualifier).

# Table of Contents

- [Qualifying for the Code Jam](#qualifying-for-the-code-jam)
- [Rules and Guidelines](#rules-and-guidelines)
- [Qualifier Assignment: The Dirty Fork](#qualifier-assignment-the-dirty-fork)
  - [Restaurant Protocol](#restaurant-protocol)
  - [The Recipe for a Restaurant](#the-recipe-for-a-restaurant)
    - [Step 1 - On Duty](#step-1---on-duty)
    - [Step 2 - Off Duty](#step-2---off-duty)
    - [Step 3 - Handling Customers](#step-3---handling-customers)
    - [Step 4 - Order Specialization](#step-4---order-specialization)

# Qualifying for the Code Jam

To qualify for the Code Jam you will be required to upload your submission to the [sign-up form](https://forms.pythondiscord.com/form/cj9-qualifier).
We set up our test suite so you don't have to worry about setting one up yourself.

Your code will be tested with a multitude of tests to test all aspects of your code making sure it works.

# Rules and Guidelines

- Your submission will be tested using a Python 3.10.5 interpreter without any additional packages installed. You're allowed to use everything included in Python's standard library, but nothing else. Please make sure to include the relevant `import` statements in your submission.

- Use [`qualifier.py`](qualifier/qualifier.py) as the base for your solution. It includes a stub for the class you need to write: `RestaurantManager`.

- Do not change the **signature** of functions included in [`qualifier.py`](qualifier/qualifier.py), and do not change the `Request` class. The test suite we will use to judge your submission relies on them. Everything else, including the docstring, may be changed.

- Do not include "debug" code in your submission. You should remove all debug prints and other debug statements before you submit your solution.

- This qualifier task is supposed to be **an individual challenge**. You should not discuss (parts of) your solution in public (including our server), or rely on others' solutions to the qualifier. Failure to meet this requirement may result in the **disqualification** of all parties involved. You are still allowed to do research and ask questions about Python as they relate to your qualifier solution, but try to use general examples if you post code along with your questions.

- You can run the tests locally by running the `unittest` suite with `python -m unittest tests.py` or `py -m unittest tests.py` from within the
`./qualifier` directory.

# Qualifier Assignment: The Dirty Fork

The Python Discord group is joining the hype of on-demand food delivery services. Our new online restaurant is called “The Dirty Fork”.
> “The lemon chicken I ordered arrived quickly and hot. My delivery driver Dave was just ducky! I highly recommend this service!”
>
>⠀⠀⠀⠀⠀⠀⠀⠀— Mr. Hem J. Lock

We would like you to create an application that takes in orders from customers, and delegates them to on-duty staff. Once the staff is done, your application should serve the finished order to the customer.

## Restaurant Protocol
In [`qualifier.py`](qualifier/qualifier.py) there is a template to start with; read the docstrings to understand what each method does.

## The Recipe for a Restaurant
### Step 1 - On Duty
Before the day begins, all staff members will send a request to the application. You can identify this by looking at the `request.scope` dictionary; the `"type"` key will be set to `"staff.onduty"`. With each staff member there will also be an ID included so that they can be identified.

An example `"staff.onduty"` request:
```json
{
	"type": "staff.onduty",
	"id": "AbCd3Fg",
	"speciality": ["meat"]
}
```

When a `"staff.onduty"` request is received, you should add their request to the `self.staff` dictionary using their ID as the key. This is so that we can keep track of who is currently working.

There is also a "speciality" key included, but you do not need to worry about that yet.

### Step 2 - Off Duty
At the end of the day, staff members will let your application know that they are going off-duty. This will be done with a new Request. You can identify an off-duty request by the Request scope key `"type"` — it will be set to `"staff.offduty"`.

An example `"staff.offduty"` request:
```json
{
	"type": "staff.offduty",
	"id": "AbCd3Fg"
}
```

When a `"staff.offduty"` request is received, the staff member must be removed from the `self.staff` dictionary, as they will no longer be accepting food orders.

> **Note**
> We will only test staff going off-duty after all orders are complete, but of course in a real application that might not be the case.

### Step 3 - Handling Customers
After all staff members have become on-duty, you will begin receiving requests from customers trying to order food.

Requests from customers can be identified by the Request's scope dictionary's `"type"` key having the value `"order"`.
```json
{
	"type": "order",
	"speciality": "meat"
}
```

When an order request is received, you should receive the full order via the `.receive()` method. Your application doesn't need to concern itself with what this order is. This object should just be:
- Passed to a selected member of staff by calling the `.send()` method.
- Afterwards, call the staff's `.receive()` method to get the result.
- And finally, pass the result back to the order using the `.send()` method.

```python
found = ...  # One selected member of staff

full_order = await request.receive()
await found.send(full_order)

result = await found.receive()
await request.send(result)
```

### Step 4 - Order Specialization
Each staff has a list of things they specialize in. You can read this from the staff's request `scope` dictionary with the `"speciality"` key (British spelling).

Example requests:
```json
{
	"type": "staff.onduty",
	"id": "AbCd3Fg",
    "speciality": ["pasta", "vegetables"]
}
```

```json
{
	"type": "order",
	"speciality": "pasta"
}
```

An order requires a certain specialty, which can be read via the order's `"speciality"` key in its `scope` dictionary. Your application should pass the order to a staff member that has the order's specialty.

> **Note**
> The `"speciality"` key is included in all `"staff.onduty"` requests, but absent from `"staff.offduty"` requests.

#### Challenge Yourself
We won't test you on how you distribute work between prioritized staff members, but in a self-respecting kitchen, work should be distributed fairly.

> **Warning**
> The tests rely on the structure of `self.staff`. If you wish to change the structure of the `self.staff` attribute at any point in this step, you can create a property named `staff` to make earlier tests still pass. It should return a dictionary with the same structure as `self.staff` used to.

## Good Luck!

![Event Banner](https://github.com/python-discord/branding/blob/main/jams/summer_code_jam_2022/site_banner.png?raw=true)
