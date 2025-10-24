# VAPI Assistant Test Script
**Comprehensive Testing Guide for Kebabalab Phone Ordering System**

---

## 📋 Pre-Test Checklist

- [ ] VAPI assistant is deployed and running
- [ ] Webhook server is accessible at your public URL
- [ ] You have VAPI credits available ($10 free = ~150-200 minutes)
- [ ] You have pen/paper to note any issues
- [ ] Call is recorded for review if needed

---

## 🎯 Testing Strategy

Each test scenario below is designed to verify specific functionality. After each order:
1. **Listen carefully** to how the AI repeats your order
2. **Verify pricing** is correct
3. **Check for bugs** (missing items, wrong prices, incorrect customizations)
4. **Complete the order** or say "cancel" to start fresh

**Tip:** You can test multiple scenarios in one call, or make separate calls for each test.

---

## TEST 1: Basic Order with Exclusions ✅
**Tests:** Item parsing, "no X" exclusions, salad/sauce detection

### Script:
```
YOU: "Hi, I'd like to order please"
AI: [Greeting]

YOU: "I'll have a large chicken kebab with lettuce, tomato, but no onion please,
      with garlic sauce and chilli sauce"
AI: [Confirms order]

YOU: "Yes that's correct"
```

### Expected Result:
- ✅ Large chicken kebab
- ✅ Lettuce and tomato included
- ✅ NO onion (exclusion working)
- ✅ Garlic and chilli sauces
- ✅ Price: $17.00

### Common Issues to Watch For:
- ❌ AI says "vertical bar" (should say comma)
- ❌ Onion is included anyway
- ❌ Wrong price

---

## TEST 2: HSP with No Cheese ✅
**Tests:** HSP parsing, cheese exclusion (Bug #1 fix)

### Script:
```
YOU: "I want a large chicken HSP with no cheese, just barbecue sauce please"
AI: [Confirms order]

YOU: "That's right"
```

### Expected Result:
- ✅ Large chicken HSP
- ✅ NO cheese (should explicitly mention no cheese)
- ✅ BBQ sauce only
- ✅ Price: $20.00

### Common Issues to Watch For:
- ❌ Cheese is included anyway (BUG #1)
- ❌ Wrong price

---

## TEST 3: Multiple Items with Quantities ✅
**Tests:** Quantity parsing, multiple items in cart

### Script:
```
YOU: "I'd like 2 small lamb kebabs and 3 Cokes please"
AI: [Confirms order]

YOU: "Yep, sounds good"
```

### Expected Result:
- ✅ 2x Small lamb kebabs ($15.00 each = $30.00)
- ✅ 3x Coke ($3.50 each = $10.50)
- ✅ Total: $40.50

### Common Issues to Watch For:
- ❌ Wrong quantity (only 1 kebab or 1 coke)
- ❌ Wrong total price

---

## TEST 4: Meal Conversion (Critical Fix) ✅
**Tests:** Converting items to meals, duplicate drink removal (Bug #2 fix from Round 1)

### Script:
```
YOU: "I want 2 small chicken kebabs and 2 Cokes"
AI: [Confirms order]

YOU: "Actually, can you make those into meals please?"
AI: [Converts to meals]

YOU: "Yes perfect"
```

### Expected Result:
- ✅ 2x Small kebab meals with Coke
- ✅ Total: $34.00 (NOT $41.00!)
- ✅ No duplicate cokes in cart

### Common Issues to Watch For:
- ❌ Total is $41.00 (duplicate drinks not removed - OLD BUG)
- ❌ 4 cokes in cart instead of 2
- ❌ Meals not created properly

---

## TEST 5: Complex Order with Multiple Customizations ✅
**Tests:** Multiple exclusions, multiple items, different customizations

### Script:
```
YOU: "I'd like 2 chicken kebabs - one with lettuce, tomato, and garlic sauce,
      and the other with no onion, no pickles, with chilli sauce and BBQ sauce"
AI: [Confirms order]

YOU: "That's correct"
```

### Expected Result:
- ✅ First kebab: lettuce, tomato, garlic sauce
- ✅ Second kebab: NO onion, NO pickles, chilli + BBQ sauce
- ✅ AI clearly distinguishes between the two kebabs

### Common Issues to Watch For:
- ❌ Both kebabs have same customizations
- ❌ Exclusions ignored
- ❌ AI confused about which kebab has what

---

## TEST 6: Editing Cart - Change Size ✅
**Tests:** editCartItem tool, size changes

### Script:
```
YOU: "I want a small chicken kebab with garlic sauce"
AI: [Confirms order]

YOU: "Actually, can you make that large instead?"
AI: [Updates size]

YOU: "Yes, that's good"
```

### Expected Result:
- ✅ Size changed from small to large
- ✅ Price updated: $12.00 → $17.00
- ✅ AI confirms the change

### Common Issues to Watch For:
- ❌ Price doesn't update
- ❌ Second item added instead of editing first

---

## TEST 7: HSP Combo Size Change (Bug #2 Fix) ✅
**Tests:** HSP combo pricing, size change recalculation

### Script:
```
YOU: "Small chicken HSP please"
AI: [Confirms order]

YOU: "Can I make that a combo with Coke?"
AI: [Converts to combo]

YOU: "Actually, change that HSP to large please"
AI: [Updates size and price]

YOU: "Perfect"
```

### Expected Result:
- ✅ Small HSP combo: $17.00
- ✅ Changed to large: $22.00 (NOT $17.00!)
- ✅ Price updated correctly

### Common Issues to Watch For:
- ❌ Price stays $17.00 (BUG #2 from Round 2 - FIXED)
- ❌ Size changes but price doesn't

---

## TEST 8: Removing Items from Cart ✅
**Tests:** removeCartItem tool

### Script:
```
YOU: "I want a large chicken kebab, a small lamb kebab, and 2 Cokes"
AI: [Confirms order]

YOU: "Actually, remove the lamb kebab please"
AI: [Removes item]

YOU: "Yes that's right"
```

### Expected Result:
- ✅ Only large chicken kebab and 2 Cokes remain
- ✅ Total price updated
- ✅ AI confirms removal

### Common Issues to Watch For:
- ❌ Wrong item removed
- ❌ Price not updated
- ❌ All items removed

---

## TEST 9: Editing Customizations ✅
**Tests:** Editing salads, sauces, protein

### Script:
```
YOU: "Large chicken kebab with lettuce and garlic sauce"
AI: [Confirms order]

YOU: "Can you change the protein to lamb please?"
AI: [Updates protein]

YOU: "And add chilli sauce as well"
AI: [Adds sauce]

YOU: "Perfect"
```

### Expected Result:
- ✅ Protein changed: chicken → lamb
- ✅ Chilli sauce added (garlic sauce still there)
- ✅ Price updated if needed

### Common Issues to Watch For:
- ❌ Protein doesn't change
- ❌ Garlic sauce removed when adding chilli
- ❌ New item created instead of editing

---

## TEST 10: Mixed Order with Everything ✅
**Tests:** Complex real-world order, multiple items, customizations, conversions

### Script:
```
YOU: "Okay, I want to place a big order. I'll have 2 large chicken kebabs -
      both with lettuce, tomato, no onion, with garlic and chilli sauce.
      Then I want a small lamb HSP with no cheese, just BBQ sauce.
      And 3 Cokes and one large chips with chicken salt please."
AI: [Confirms order]

YOU: "Actually, can you make those 2 kebabs into meals with the Cokes?"
AI: [Converts to meals]

YOU: "Yes, and the rest is separate. That's correct."
```

### Expected Result:
- ✅ 2x Large chicken kebab meals with Coke (lettuce, tomato, no onion, garlic + chilli)
- ✅ 1x Small lamb HSP (no cheese, BBQ sauce)
- ✅ 1x Coke (separate)
- ✅ 1x Large chips with chicken salt
- ✅ Total: $44.00 + $15.00 + $3.50 + $9.00 = $71.50

### Common Issues to Watch For:
- ❌ Duplicate cokes (should only be 3 total: 2 in meals + 1 separate)
- ❌ Cheese on HSP
- ❌ Onions on kebabs
- ❌ Wrong pricing

---

## TEST 11: Size Confirmation (Never Default) ✅
**Tests:** AI asks for size if not specified

### Script:
```
YOU: "I want a chicken kebab"
AI: [Should ask: "Would you like small or large?"]

YOU: "Large please"
AI: [Confirms order]

YOU: "Yes that's right"
```

### Expected Result:
- ✅ AI MUST ask for size (never defaults)
- ✅ Large kebab added after you specify
- ✅ Price: $17.00

### Common Issues to Watch For:
- ❌ AI defaults to small (should never happen)
- ❌ AI doesn't ask for size clarification

---

## TEST 12: Edge Case - Change Everything ✅
**Tests:** Multiple edits, system stability

### Script:
```
YOU: "Small chicken kebab with lettuce and garlic sauce"
AI: [Confirms order]

YOU: "Change it to large"
AI: [Updates size]

YOU: "Actually make it lamb"
AI: [Updates protein]

YOU: "Add chilli sauce too"
AI: [Adds sauce]

YOU: "Remove the lettuce"
AI: [Removes salad]

YOU: "Make it a combo with Sprite"
AI: [Converts to meal]

YOU: "Perfect, that's it"
```

### Expected Result:
- ✅ Final order: Large lamb kebab meal with Sprite, garlic + chilli sauce, no lettuce
- ✅ All edits processed correctly
- ✅ Correct pricing throughout

### Common Issues to Watch For:
- ❌ System gets confused with multiple edits
- ❌ Previous edits lost
- ❌ Wrong final order

---

## TEST 13: Checkout and Payment ✅
**Tests:** Complete order flow, payment processing

### Script:
```
YOU: "I want a large chicken kebab with garlic sauce"
AI: [Confirms order]

YOU: "Yes, I'm ready to checkout"
AI: [Provides total, asks for payment method]

YOU: "Cash please"
AI: [Confirms cash payment]

YOU: "Yes"
AI: [Finalizes order, provides order number and ETA]
```

### Expected Result:
- ✅ Order total correct
- ✅ Cash payment recorded
- ✅ Order number provided
- ✅ ETA mentioned (20-25 minutes)
- ✅ Order saved to database

### Common Issues to Watch For:
- ❌ Wrong total
- ❌ Payment method not recorded
- ❌ No order confirmation

---

## TEST 14: Cancel and Start Over ✅
**Tests:** Cart clearing, new order

### Script:
```
YOU: "I want 2 large chicken kebabs"
AI: [Confirms order]

YOU: "Actually, cancel that order please"
AI: [Clears cart]

YOU: "Start a new order - I want a small lamb HSP"
AI: [Starts fresh order]

YOU: "Yes that's right"
```

### Expected Result:
- ✅ First order cancelled
- ✅ Cart cleared
- ✅ New order starts fresh
- ✅ Only HSP in cart

### Common Issues to Watch For:
- ❌ Old items still in cart
- ❌ Cart not cleared

---

## 📊 Testing Checklist Summary

After completing all tests, verify:

### Core Functionality:
- [ ] Basic orders work (kebabs, HSPs, chips, drinks)
- [ ] Size parsing works (small/large)
- [ ] Protein parsing works (chicken/lamb/mixed)
- [ ] Quantity parsing works (1, 2, 3, etc.)

### Customizations:
- [ ] Salads added correctly (lettuce, tomato, onion, pickles)
- [ ] Sauces added correctly (garlic, chilli, BBQ, etc.)
- [ ] Extras work (cheese, haloumi, extra meat)

### Exclusions (Critical):
- [ ] "No onion" works on kebabs
- [ ] "No cheese" works on HSPs
- [ ] "No pickles", "no tomato" etc. work
- [ ] "Without X" and "hold X" patterns work

### Cart Operations:
- [ ] Adding items works
- [ ] Removing items works
- [ ] Editing size works
- [ ] Editing protein works
- [ ] Editing salads/sauces works
- [ ] Quantity changes work

### Meal/Combo Conversions:
- [ ] Converting kebabs to meals works
- [ ] Duplicate drinks removed correctly
- [ ] Meal pricing correct ($17/$22 for small/large)
- [ ] HSP combos work ($17/$22 for small/large)

### Critical Bug Fixes:
- [ ] "No onion" exclusion works (Round 1 Bug #1)
- [ ] Duplicate drinks removed in meal conversion (Round 1 Bug #2)
- [ ] Speech output natural, no "vertical bar" (Round 1 Bug #3)
- [ ] "No cheese" exclusion works (Round 2 Bug #1)
- [ ] HSP combo size change updates price (Round 2 Bug #2)

### Pricing:
- [ ] All individual item prices correct
- [ ] Meal prices correct ($17 small, $22 large)
- [ ] HSP combo prices correct ($17 small, $22 large)
- [ ] Chip upgrade pricing works ($3 extra for large chips)
- [ ] Total calculations correct

### User Experience:
- [ ] AI asks for size if not specified
- [ ] AI reads orders naturally (commas, not pipes)
- [ ] AI confirms changes clearly
- [ ] AI handles multiple edits gracefully
- [ ] Checkout flow smooth

---

## 🐛 Bug Reporting Template

If you find issues during testing, document them like this:

```
BUG: [Short description]
Test: [Which test scenario]
Time: [Timestamp in call]
Expected: [What should happen]
Actual: [What actually happened]
Severity: [Critical/High/Medium/Low]

Example:
BUG: Onion still added despite saying "no onion"
Test: TEST 1 - Basic Order with Exclusions
Time: 2:35 in call
Expected: No onion in kebab
Actual: Kebab has onion
Severity: Critical
```

---

## 💡 Pro Tips for Testing

1. **Test one scenario at a time** - Don't rush through all tests in one call
2. **Listen carefully** to how AI repeats your order
3. **Speak clearly** - VAPI speech recognition needs clear input
4. **Use natural language** - Test how real customers would order
5. **Take notes** - Write down any issues immediately
6. **Check logs** - Review server logs after calls for debugging
7. **Test edge cases** - Try to break it with weird orders
8. **Verify pricing** - Always check the total matches your expectation

---

## 📈 Expected Results Summary

If all tests pass, you should see:

```
✅ 14/14 test scenarios passed
✅ All exclusions working (no onion, no cheese, etc.)
✅ All pricing correct
✅ All edits processed properly
✅ All conversions working (meals, combos)
✅ No duplicate items
✅ Natural speech output
✅ Smooth checkout flow

🎉 SYSTEM READY FOR PRODUCTION
```

---

## 🚨 Known Issues (Should All Be Fixed)

These were bugs we fixed - verify they're actually resolved:

1. ~~"No onion" ignored~~ → FIXED (Round 1)
2. ~~Duplicate drinks in meal conversion~~ → FIXED (Round 1)
3. ~~AI saying "vertical bar"~~ → FIXED (Round 1)
4. ~~"No cheese" on HSP ignored~~ → FIXED (Round 2)
5. ~~HSP combo size change doesn't update price~~ → FIXED (Round 2)

**If any of these still occur, STOP and investigate immediately.**

---

## 📞 After Testing

Once testing is complete:

1. **Review call recordings** in VAPI dashboard
2. **Check server logs** for any errors
3. **Document any bugs** found
4. **Calculate success rate** (tests passed / total tests)
5. **Decide if ready for production** or needs more fixes

---

**Good luck with testing! You've got a comprehensive test suite now.** 🚀

**Remember:** Your webhook code is already 100% tested locally (45/45 tests passing). This VAPI testing is specifically for the voice conversation layer, speech recognition, and end-to-end flow.
