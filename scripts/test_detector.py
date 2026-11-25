import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "loopbench")); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#!/usr/bin/env python3
"""Hand test for loop_detect.py: 10 looping + 10 clean outputs. Must pass 20/20."""
from loop_detect import detect

LOOPING = [
    # 1: same sentence x4
    ("The train speed is 60 km/h so the time is four hours for this trip. " * 4) + "Therefore done.",
    # 2: repeated verification sentence
    "Let me verify the calculation once more to be completely sure about it. " * 3 + "x = 5.",
    # 3: 8-gram repeat inside varied text
    "First we compute the total cost of all the items in the basket today. Then we check. "
    "Again we compute the total cost of all the items in the basket today carefully. "
    "Once more we compute the total cost of all the items in the basket today now.",
    # 4: reasoning circle
    "So the answer depends on the value of the unknown variable in the equation. " * 3,
    # 5: repeated step phrase
    "Step one is to multiply both sides of the equation by the common denominator. " * 3 + "end",
    # 6: word salad loop
    "the result is the result is the result is " * 6,
    # 7: long repeated clause
    "Because the function returns the sum of the two input values each time it is called here " * 3,
    # 8: re-verification loop
    "I will check the arithmetic again from the beginning to make sure nothing is wrong. " * 3,
    # 9: near-sentence repeat with tiny variations stripped by normalization
    "The total number of apples in the box is twenty four as counted before now. " * 3,
    # 10: non-termination only
    "Some normal reasoning that just keeps going without a final answer marker",
]

CLEAN = [
    # 1: normal short reasoning
    "The train covers 240 km in 3 hours, so its speed is 80 km/h. In the next 2 hours it covers 180 km at 90 km/h. Total distance is 420 km in 5 hours, so the average speed is 84 km/h. Final answer: 84 km/h.",
    # 2: code with legitimate repetition (masked)
    "Here is the function:\n```python\nfor i in range(10):\n    print(i)\n    total += i\nfor i in range(10):\n    print(i)\n    total += i\n```\nIt prints numbers twice as requested.",
    # 3: a list (short items, no 10-word sentence repeats)
    "Fruits: apple, banana, cherry, dates, elderberry, fig, grape, honeydew, kiwi, lemon, mango, nectarine, orange, papaya, quince, raspberry, strawberry, tangerine.",
    # 4: restating the question once
    "The question asks for the average speed over the whole journey. We add distances and times separately, then divide. Final answer: 84 km/h.",
    # 5: longer explanation, no repeats
    "Photosynthesis converts sunlight, water and carbon dioxide into oxygen and glucose inside plant cells. Chlorophyll in the leaves absorbs light, mainly blue and red wavelengths. The process has two stages, the light reactions and the Calvin cycle, which together store energy in chemical bonds for later use by the plant.",
    # 6: two similar but not identical sentences
    "He first added the numbers to get a subtotal for the month of January sales. Later she added the numbers to get a subtotal for the month of February sales.",
    # 7: math steps all different
    "Start with 5x + 3 = 23. Subtract 3 from both sides to get 5x = 20. Divide both sides by 5 to isolate the variable. So x equals 4. Final answer: 4.",
    # 8: repeated short phrase under thresholds (only 2x, short sentence)
    "Check the units. Check the units. Then write the final answer below the working.",
    # 9: quotation repeated once
    "As the proverb says, a stitch in time saves nine in the end. Remember, a stitch in time saves nine.",
    # 10: long clean reasoning with varied steps
    "We need the least common multiple of 12 and 18 for the schedule problem today. Prime factors of 12 are two squared times three, and for 18 they are two times three squared. Taking the highest powers gives four times nine, which is thirty six. So the buses meet again after 36 minutes. Final answer: 36 minutes.",
]

fails = 0
for i, t in enumerate(LOOPING, 1):
    kw = {"hit_token_cap": True, "has_final_answer": False} if i == 10 else {}
    r = detect(t, **kw)
    ok = r["loop"] is True
    print(f"LOOP case {i}: {'PASS' if ok else 'FAIL'} -> {r['loop']}")
    fails += 0 if ok else 1
for i, t in enumerate(CLEAN, 1):
    r = detect(t)
    ok = r["loop"] is False
    print(f"CLEAN case {i}: {'PASS' if ok else 'FAIL'} -> {r['loop']} {r['ngram_hits'] if not ok else ''}")
    fails += 0 if ok else 1
print(f"\n{20 - fails}/20 passed")
