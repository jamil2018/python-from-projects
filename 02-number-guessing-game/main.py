import random

while True:
    random_number = random.randint(1, 100)

    print("I am thinking of a number between 1 and 100.")
    attempt_counter = 0

    while True:
        try:
            user_guess = int(input("Your Guess: "))
        except:
            print("Invalid value. Please enter a integer number.")
            continue

        if user_guess > 100 or user_guess < 1:
            print("Number have to be between 1 and 100")
        elif user_guess > random_number:
            print("Too high.")
            attempt_counter += 1
        elif user_guess < random_number:
            print("Too low.")
            attempt_counter += 1
        elif user_guess == random_number:
            print(f"Correct! You got it in {attempt_counter} attempts.")
            break

    continuation_choice = input("Play again? (y/n): ").lower()

    if continuation_choice == "y":
        continue
    if continuation_choice == "n":
        break
