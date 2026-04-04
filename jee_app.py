# Babu's JEE Practice App
print("--- WELCOME TO BABU'S JEE APP ---")

def physics_quiz():
    ans = input("\nWhat is the unit of Force? (Newton/Joule): ")
    if ans.lower() == "newton":
        print("✅ Correct! Sabash Babu.")
    else:
        print("❌ Wrong. Try again!")

physics_quiz()
