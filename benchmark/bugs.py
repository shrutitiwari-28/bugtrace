"""Benchmark bugs for BugTrace.

Every bug has:
  source      the buggy code (saved as calculator.py in the sandbox)
  test        the approved test: it fails on the bug and defines what "fixed" means
  regression  tests that already pass on the buggy code and must keep passing
  reference   a known-good fix, used only to prove the bug is valid
              (the AI never sees it)
The AI only ever sees: source, error, expected.
"""


def _t(names, body):
    return f"from calculator import {names}\n\n{body}"


BUGS = [
    # ---------------- tuning set (10): you may improve prompts using these ----------------
    dict(
        id="B01", split="tuning", category="empty input",
        error="ZeroDivisionError: division by zero when numbers is []",
        expected="calculate_average returns None for an empty list. Otherwise it returns the arithmetic average.",
        source="def calculate_average(numbers):\n    return sum(numbers) / len(numbers)\n",
        reference="def calculate_average(numbers):\n    if not numbers:\n        return None\n    return sum(numbers) / len(numbers)\n",
        test=_t("calculate_average", "def test_empty_returns_none():\n    assert calculate_average([]) is None\n"),
        regression=_t("calculate_average", "def test_normal():\n    assert calculate_average([2, 4, 6]) == 4\n\ndef test_single():\n    assert calculate_average([5]) == 5\n"),
    ),
    dict(
        id="B02", split="tuning", category="off-by-one",
        error="first_n([1, 2, 3], 2) returned [1] but should return [1, 2]",
        expected="first_n(items, n) returns the first n items of the list.",
        source="def first_n(items, n):\n    return items[:n - 1]\n",
        reference="def first_n(items, n):\n    return items[:n]\n",
        test=_t("first_n", "def test_first_two():\n    assert first_n([1, 2, 3], 2) == [1, 2]\n"),
        regression=_t("first_n", "def test_empty():\n    assert first_n([], 2) == []\n\ndef test_zero():\n    assert first_n([1], 0) == []\n"),
    ),
    dict(
        id="B03", split="tuning", category="wrong dictionary key",
        error="KeyError: 'mail' when calling get_email({'name': 'Ana', 'email': 'ana@example.com'})",
        expected="get_email returns the value stored under the 'email' key.",
        source="def get_email(user):\n    return user['mail']\n\ndef get_name(user):\n    return user['name']\n",
        reference="def get_email(user):\n    return user['email']\n\ndef get_name(user):\n    return user['name']\n",
        test=_t("get_email", "def test_email():\n    assert get_email({'name': 'Ana', 'email': 'ana@example.com'}) == 'ana@example.com'\n"),
        regression=_t("get_name", "def test_name():\n    assert get_name({'name': 'Ana'}) == 'Ana'\n"),
    ),
    dict(
        id="B04", split="tuning", category="None handling",
        error="TypeError: can only concatenate str (not 'NoneType') to str when last is None",
        expected="If last is None, full_name returns just the first name.",
        source="def full_name(first, last):\n    return first + ' ' + last\n",
        reference="def full_name(first, last):\n    if last is None:\n        return first\n    return first + ' ' + last\n",
        test=_t("full_name", "def test_no_last_name():\n    assert full_name('Ada', None) == 'Ada'\n"),
        regression=_t("full_name", "def test_both():\n    assert full_name('Ada', 'Lovelace') == 'Ada Lovelace'\n"),
    ),
    dict(
        id="B05", split="tuning", category="wrong condition",
        error="is_adult(18) returned False",
        expected="A person aged 18 or older is an adult.",
        source="def is_adult(age):\n    return age > 18\n",
        reference="def is_adult(age):\n    return age >= 18\n",
        test=_t("is_adult", "def test_eighteen():\n    assert is_adult(18) is True\n"),
        regression=_t("is_adult", "def test_older():\n    assert is_adult(30) is True\n\ndef test_younger():\n    assert is_adult(10) is False\n"),
    ),
    dict(
        id="B06", split="tuning", category="boundary error",
        error="clamp(15, 0, 10) returned 0 but should return 10",
        expected="clamp limits a value to the range from low to high.",
        source="def clamp(value, low, high):\n    if value < low:\n        return low\n    if value > high:\n        return low\n    return value\n",
        reference="def clamp(value, low, high):\n    if value < low:\n        return low\n    if value > high:\n        return high\n    return value\n",
        test=_t("clamp", "def test_above_range():\n    assert clamp(15, 0, 10) == 10\n"),
        regression=_t("clamp", "def test_inside():\n    assert clamp(5, 0, 10) == 5\n\ndef test_below():\n    assert clamp(-3, 0, 10) == 0\n"),
    ),
    dict(
        id="B07", split="tuning", category="wrong return value",
        error="largest([3, 9, 2]) returned 2 but should return 9",
        expected="largest returns the biggest number in a non-empty list.",
        source="def largest(numbers):\n    best = numbers[0]\n    for n in numbers:\n        if n < best:\n            best = n\n    return best\n",
        reference="def largest(numbers):\n    best = numbers[0]\n    for n in numbers:\n        if n > best:\n            best = n\n    return best\n",
        test=_t("largest", "def test_largest():\n    assert largest([3, 9, 2]) == 9\n"),
        regression=_t("largest", "def test_single():\n    assert largest([4]) == 4\n"),
    ),
    dict(
        id="B08", split="tuning", category="string handling",
        error="is_palindrome('Race car') returned False",
        expected="is_palindrome ignores case and spaces.",
        source="def is_palindrome(text):\n    return text == text[::-1]\n",
        reference="def is_palindrome(text):\n    cleaned = text.replace(' ', '').lower()\n    return cleaned == cleaned[::-1]\n",
        test=_t("is_palindrome", "def test_mixed_case_and_space():\n    assert is_palindrome('Race car') is True\n"),
        regression=_t("is_palindrome", "def test_yes():\n    assert is_palindrome('level') is True\n\ndef test_no():\n    assert is_palindrome('hello') is False\n"),
    ),
    dict(
        id="B09", split="tuning", category="accumulator bug",
        error="running_total([1, 2, 3]) returned [1, 2, 3] but should return [1, 3, 6]",
        expected="running_total returns the cumulative sum after each number.",
        source="def running_total(numbers):\n    result = []\n    total = 0\n    for n in numbers:\n        total = n\n        result.append(total)\n    return result\n",
        reference="def running_total(numbers):\n    result = []\n    total = 0\n    for n in numbers:\n        total += n\n        result.append(total)\n    return result\n",
        test=_t("running_total", "def test_cumulative():\n    assert running_total([1, 2, 3]) == [1, 3, 6]\n"),
        regression=_t("running_total", "def test_empty():\n    assert running_total([]) == []\n\ndef test_single():\n    assert running_total([4]) == [4]\n"),
    ),
    dict(
        id="B10", split="tuning", category="integer division",
        error="percent(1, 4) returned 0 but should return 25",
        expected="percent(part, whole) returns part as a percentage of whole.",
        source="def percent(part, whole):\n    return part // whole * 100\n",
        reference="def percent(part, whole):\n    return part / whole * 100\n",
        test=_t("percent", "def test_quarter():\n    assert percent(1, 4) == 25\n"),
        regression=_t("percent", "def test_zero():\n    assert percent(0, 5) == 0\n\ndef test_all():\n    assert percent(5, 5) == 100\n"),
    ),
    # ---------------- held-out set (5): freeze the code, then run once, no tuning ----------------
    dict(
        id="B11", split="heldout", category="duplicates",
        error="unique([3, 1, 3, 2, 1]) returned [1, 2, 3] but should return [3, 1, 2]",
        expected="unique removes duplicates and keeps the order in which items first appear.",
        source="def unique(items):\n    return list(set(items))\n",
        reference="def unique(items):\n    seen = []\n    for item in items:\n        if item not in seen:\n            seen.append(item)\n    return seen\n",
        test=_t("unique", "def test_keeps_order():\n    assert unique([3, 1, 3, 2, 1]) == [3, 1, 2]\n"),
        regression=_t("unique", "def test_empty():\n    assert unique([]) == []\n\ndef test_single():\n    assert unique([1]) == [1]\n"),
    ),
    dict(
        id="B12", split="heldout", category="shared default argument",
        error="add_item('b') returned ['a', 'b'] after an earlier add_item('a') call",
        expected="Each call without a list argument starts with a new empty list.",
        source="def add_item(item, items=[]):\n    items.append(item)\n    return items\n",
        reference="def add_item(item, items=None):\n    if items is None:\n        items = []\n    items.append(item)\n    return items\n",
        test=_t("add_item", "def test_fresh_list_each_call():\n    add_item('a')\n    assert add_item('b') == ['b']\n"),
        regression=_t("add_item", "def test_given_list():\n    assert add_item('x', ['y']) == ['y', 'x']\n"),
    ),
    dict(
        id="B13", split="heldout", category="whitespace handling",
        error="word_count('a  b') returned 3 but should return 2",
        expected="word_count counts words separated by any amount of whitespace.",
        source="def word_count(text):\n    return len(text.split(' '))\n",
        reference="def word_count(text):\n    return len(text.split())\n",
        test=_t("word_count", "def test_double_space():\n    assert word_count('a  b') == 2\n"),
        regression=_t("word_count", "def test_three():\n    assert word_count('one two three') == 3\n\ndef test_one():\n    assert word_count('hi') == 1\n"),
    ),
    dict(
        id="B14", split="heldout", category="wrong sort order",
        error="top_scores([5, 1, 9, 7], 2) returned [1, 5] but should return [9, 7]",
        expected="top_scores returns the n highest scores, highest first.",
        source="def top_scores(scores, n):\n    return sorted(scores)[:n]\n",
        reference="def top_scores(scores, n):\n    return sorted(scores, reverse=True)[:n]\n",
        test=_t("top_scores", "def test_highest_first():\n    assert top_scores([5, 1, 9, 7], 2) == [9, 7]\n"),
        regression=_t("top_scores", "def test_empty():\n    assert top_scores([], 3) == []\n\ndef test_single():\n    assert top_scores([4], 1) == [4]\n"),
    ),
    dict(
        id="B15", split="heldout", category="wrong formula",
        error="apply_discount(200, 10) returned 199.9 but should return 180",
        expected="apply_discount(price, percent) reduces the price by that percentage.",
        source="def apply_discount(price, percent):\n    return price - percent / 100\n",
        reference="def apply_discount(price, percent):\n    return price - price * percent / 100\n",
        test=_t("apply_discount", "def test_ten_percent():\n    assert apply_discount(200, 10) == 180\n"),
        regression=_t("apply_discount", "def test_no_discount():\n    assert apply_discount(50, 0) == 50\n"),
    ),
]
