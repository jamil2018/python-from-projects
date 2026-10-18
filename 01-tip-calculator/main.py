print("Welcome to the tip calculator!")
total_bill = float(input("Total bill: "))
tip_percent = float(input("Tip percentage (e.g. 10, 15, 20): "))
total_people = int(input("How many people? Answer: "))

if total_people == 0:
    print("Number of people cannot be zero!")
    exit(0)


tip_amount = (total_bill * tip_percent) / 100
total_payable_bill = total_bill + tip_amount

amount_payable_per_person = total_payable_bill / total_people

print(f"Tip: {tip_amount:.2f}")
print(f"Total: {total_payable_bill:.2f}")
print(f"Each person: {amount_payable_per_person:.2f}")
