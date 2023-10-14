import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk

# Determine base path
if getattr(sys, 'frozen', False):
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.dirname(__file__)

icon_path = os.path.join(BASE_PATH, 'icon', 'app.ico')


# This ensures that sv_ttk uses the correct path when looking for its theme files
# Assuming the library looks for themes relatively, modify it to use the absolute path.
sv_ttk.THEME_PATH = os.path.join(BASE_PATH, 'theme')  

class CombatCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        sv_ttk.set_theme("dark")
        self.iconbitmap(default=icon_path)
        self.title("Pixel's Combat Lvl Calculator")
        self.resizable(False, False)  # Prevent resizing in both dimensions
        stats = ["attack", "strength", "defence", "hitpoints", "prayer", "ranged", "magic", "combat"]
        self.entries = {}
        self.lock_vars = {}
        self.lock_checkboxes = {}

        for i, stat in enumerate(stats):
            ttk.Label(self, text=stat.capitalize()).grid(row=i, column=0, sticky="w", padx=10, pady=5)
            entry = ttk.Entry(self)
            entry.insert(0, '1')  # Insert '1' as the default value
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[stat] = entry

            lock_var = tk.BooleanVar(self)
            lock_checkbox = ttk.Checkbutton(self, text="Lock", variable=lock_var)
            lock_checkbox.grid(row=i, column=2, padx=10, pady=5)
            lock_checkbox.grid_remove()  # Hide lock checkboxes initially
            self.lock_vars[stat] = lock_var
            self.lock_checkboxes[stat] = lock_checkbox
        
        # Mode switch button
        self.calc_mode = tk.BooleanVar(self, value=True)
        self.mode_button = ttk.Button(self, text="Mode: Calculate Combat Level", command=self.toggle_mode)
        self.mode_button.grid(row=len(stats), column=0, columnspan=2, pady=10, sticky="ew")
        
        ttk.Button(self, text="Calculate", command=self.on_calculate).grid(row=len(stats)+1, column=0, columnspan=3, pady=10)
        self.result_label = ttk.Label(self, text="")
        self.result_label.grid(row=len(stats)+2, column=0, columnspan=3, pady=10)
        
    def toggle_mode(self):
        # Switch between combat level and missing skills
        if self.calc_mode.get():
            # Switching to missing skills mode
            self.calc_mode.set(False)
            self.entries['combat'].config(state='normal')
            self.mode_button.config(text="Mode: Calculate Combat Level")
            for checkbox in self.lock_checkboxes.values():
                checkbox.grid()  # Show lock checkboxes
        else:
            # Switching to combat level mode
            self.calc_mode.set(True)
            self.entries['combat'].config(state='disabled')
            self.mode_button.config(text="Mode: Calculate Missing Levels")
            for checkbox in self.lock_checkboxes.values():
                checkbox.grid_remove()  # Hide lock checkboxes

    def on_calculate(self):
        stats = {}
        for stat, entry in self.entries.items():
            try:
                stats[stat] = float(entry.get())
            except ValueError:
                stats[stat] = 0

        # Check if combat level exceeds 10,000
        if stats['combat'] > 10000:
            messagebox.showwarning("Warning", "Combat level cannot exceed 10,000!")  # Show a warning popup
            return
        
        if self.calc_mode.get():
            # Calculate Combat Level
            combat_level = calculate_combat_level(stats)
            self.result_label.config(text=f"Combat Level: {combat_level:.2f}")
        else:
            # Calculate Missing Skills
            missing_levels = calculate_missing_levels(stats)
            if not missing_levels:  # If no more levels are required
                self.result_label.config(text="You already have the required levels!")
            else:
                self.result_label.config(text=f"Missing Levels:\n {missing_levels}")


def calculate_combat_level(stats):
    # Step 1: Calculate base combat level
    prayer_part = stats['prayer'] // 2
    base = 0.25 * (stats['hitpoints'] + stats['defence'] + prayer_part)
    
    # Step 2: Calculate melee combat level
    melee = 0.325 * (stats['attack'] + stats['strength'])
    melee_combat = base + melee
    
    # Step 3: Calculate magic or ranged level, whichever is higher
    magic_effective = stats['magic'] // 2 + stats['magic']
    ranged_effective = stats['ranged'] // 2 + stats['ranged']  # Similar formula for ranged
    highest_effective = max(magic_effective, ranged_effective)
    
    magic_or_ranged_combat = base + 0.325 * highest_effective
    
    # Final step: Return the highest of melee or magic/ranged combat level
    return max(melee_combat, magic_or_ranged_combat)

def calculate_missing_levels(stats):
    desired_combat_level = stats['combat']
    
    # Unlock all stats, then remove locked ones
    unlocked_stats = list(stats.keys())
    unlocked_stats.remove('combat')
    for stat, lock_var in app.lock_vars.items():
        if lock_var.get():
            unlocked_stats.remove(stat)
    
    computed_level = calculate_combat_level(stats)
    if computed_level >= desired_combat_level:
        return None  # Return None if no more levels are required
    
    # Iteratively increase the levels of unlocked stats
    while computed_level < desired_combat_level:
        for stat in unlocked_stats:
            stats[stat] += 1
        computed_level = calculate_combat_level(stats)

    # Calculate the number of levels added to each stat to achieve the combat level
    delta_levels = {stat: stats[stat] - float(app.entries[stat].get()) for stat in unlocked_stats}
    
    # Return the skills and their deltas in a newline-separated format
    return '\n'.join([f"{stat.capitalize()}: +{delta}" for stat, delta in delta_levels.items() if delta > 0])

if __name__ == "__main__":
    app = CombatCalculator()
    app.mainloop()