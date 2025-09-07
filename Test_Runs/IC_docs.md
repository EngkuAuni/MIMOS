# IC Design specifications for a 

## User Flow
[1] User enters spec → HDL is generated
     ↳ Fails validation? Show warning + let user fix in text area
     ↳ Passes validation? Proceed

[2] User reviews HDL → manually edits if needed → clicks "Generate Testbench"

[3] If testbench fails → show fallback or error explanation

[4] Run simulation
