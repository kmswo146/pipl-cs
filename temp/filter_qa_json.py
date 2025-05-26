import json

# Path to your input and output files
input_file = "qa_candidates_20250525_180436.json"
output_file = "qa_candidates_filtered.json"

# Load the JSON data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

qa_candidates = data.get("qa_candidates", [])
kept_candidates = []

print(f"Total questions: {len(qa_candidates)}")
print("Press 'd' to delete, 'k' to keep, or 'q' to quit and save progress.\n")

for idx, qa in enumerate(qa_candidates):
    print(f"\n[{idx+1}/{len(qa_candidates)}]")
    print("Q:", qa["question"])
    print("A:", qa["answer"])
    print("Topic:", qa.get("topic", ""))
    while True:
        action = input("Keep or delete? (k/d/q): ").strip().lower()
        if action == "k":
            kept_candidates.append(qa)
            break
        elif action == "d":
            break
        elif action == "q":
            print("Quitting early and saving progress...")
            break
        else:
            print("Invalid input. Please enter 'k', 'd', or 'q'.")
    if action == "q":
        break

# Save the filtered data
data["qa_candidates"] = kept_candidates
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nFiltered file saved as {output_file}. Kept {len(kept_candidates)} questions.")