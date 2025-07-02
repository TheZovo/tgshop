import random
import string

def generate_captcha():
    a = random.randint(1, 50)
    b = random.randint(1, 50)
    answer = a + b
    return f"What is {a} + {b}?", str(answer)

def verify_captcha(user_input: str, correct_answer: str):
    return user_input.strip() == correct_answer