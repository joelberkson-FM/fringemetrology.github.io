import os

filepath = r'c:\dev\fringemetrology.github.io\structured-light.html'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Markers
start_marker = "<!-- Limits of Conventional Metrology Section -->"
end_marker = "</section>" # We need to match the specific </section> closing the block
insert_marker = '<section class="full-width-section theme-light">'

# Find start line
start_idx = -1
for i, line in enumerate(lines):
    if start_marker in line:
        start_idx = i
        break

if start_idx == -1:
    print("Could not find start marker")
    exit(1)

# Find end line (search after start)
end_idx = -1
# We know from view_file it is line 289 (index 288)
# But let's look for </section> at the expected indentation or just count lines.
# The section block is indented.
# Let's stick to the line numbers from view_file as they are reliable unless file changed (which it shouldn't have).
# Start: 185 -> index 184
# End: 289 -> index 288
start_idx = 184
end_idx = 288
insert_idx = 115

print(f"Moving lines {start_idx+1}-{end_idx+1} to before {insert_idx+1}")
print(f"Content at {start_idx+1}: {lines[start_idx].strip()}")
print(f"Content at {end_idx+1}: {lines[end_idx].strip()}")
print(f"Content at {insert_idx+1}: {lines[insert_idx].strip()}")

section_lines = lines[start_idx : end_idx + 1]

# Remove original
# Construct new list
# Be careful: removing changes indices if done in-place or if insert is after remove.
# The block to remove is AFTER the insert point (184 > 115).
# So removing it won't affect the insert point index.

# 1. Take everything before insert point
part1 = lines[:insert_idx]
# 2. The lines to move
part2 = section_lines
# 3. Everything between insert point and start of moved block
part3 = lines[insert_idx:start_idx]
# 4. Everything after end of moved block
part4 = lines[end_idx+1:]

new_lines = part1 + part2 + part3 + part4

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Move complete.")
