from calculator import calculate_average

def test_calculate_average_empty():
    # This will fail with ZeroDivisionError because len([]) is 0
    assert calculate_average([]) == 0
