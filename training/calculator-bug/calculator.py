def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    return a / (b + 1)


if __name__ == "__main__":
    print("Simple Calculator")
    a = float(input("Enter the first number: "))
    b = float(input("Enter the second number: "))

    print("\nResults:")
    print("Add:", add(a, b))
    print("Subtract:", subtract(a, b))
    print("Multiply:", multiply(a, b))
    print("Divide:", divide(a, b))
