import sys
import os
import tkinter as tk
import re
from tkinter import ttk, messagebox, simpledialog
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
        self.attributes('-topmost', True)  # This line sets the window to be always on top
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
        self.mode_button.grid(row=len(stats), column=0, columnspan=3, pady=10, sticky="ew")
        
        ttk.Button(self, text="Calculate", command=self.on_calculate).grid(row=len(stats)+1, column=0, columnspan=3, pady=10)
        self.result_label = ttk.Label(self, text="")
        self.result_label.grid(row=len(stats)+2, column=0, columnspan=3, pady=10)
        
    def toggle_mode(self):
        # Switch between combat level and missing skills
        if self.calc_mode.get():
            # Switching to missing skills mode
            self.calc_mode.set(False)
            self.entries['combat'].config(state='normal')
            self.mode_button.config(text="Mode: Calculate Missing Levels")
            for checkbox in self.lock_checkboxes.values():
                checkbox.grid()  # Show lock checkboxes

            # Create new entries for offensive bonus and base damage if they don't exist
            if 'offensive_bonus' not in self.entries:
                self.create_additional_entries()

        else:
            # Switching to combat level mode
            self.calc_mode.set(True)
            self.entries['combat'].config(state='disabled')
            self.mode_button.config(text="Mode: Calculate Combat Level")
            for checkbox in self.lock_checkboxes.values():
                checkbox.grid_remove()  # Hide lock checkboxes

            # Remove entries for offensive bonus and base damage
            if 'offensive_bonus' in self.entries:
                self.remove_additional_entries()

    def create_additional_entries(self):
        self.additional_labels = {}  # Store the labels for additional stats
        additional_stats = ["offensive_bonus", "base_damage"]
        for i, stat in enumerate(additional_stats, start=len(self.entries)):
            label = ttk.Label(self, text=stat.capitalize().replace('_', ' '))
            label.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            self.additional_labels[stat] = label  # Store the label

            entry = ttk.Entry(self)
            entry.insert(0, '0')  # Insert '0' as the default value
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries[stat] = entry

        # Re-position mode button, calculate button, and result label
        self.reposition_ui_elements(len(self.entries))

    def remove_additional_entries(self):
        for stat in ["offensive_bonus", "base_damage"]:
            self.additional_labels[stat].grid_remove()  # Remove the label from the grid
            del self.additional_labels[stat]  # Delete the label reference

            self.entries[stat].grid_remove()  # Remove the entry from the grid
            del self.entries[stat]  # Delete the entry reference

        # Re-position mode button, calculate button, and result label after removing entries
        self.reposition_ui_elements(len(self.entries) + 1)

    def reposition_ui_elements(self, start_row):
        # Update the positions of the mode button, calculate button, and result label
        self.mode_button.grid(row=start_row, column=0, columnspan=2, pady=10, sticky="ew")
        calculate_button_row = start_row + 1
        self.children['!button2'].grid(row=calculate_button_row, column=0, columnspan=3, pady=10)  # calculate button
        self.result_label.grid(row=calculate_button_row + 1, column=0, columnspan=3, pady=10)

    def prompt_offensive_skill(self, offensive_level):
        dialog = OffensiveSkillDialog(self, offensive_level)
        self.wait_window(dialog)  # This makes the dialog modal
        return dialog.selected_skill
    
    def on_calculate(self):
        stats = {}
        for stat, entry in self.entries.items():
            try:
                # Ensure offensive_bonus and base_damage are not included as levels
                if stat not in ["offensive_bonus", "base_damage"]:
                    stats[stat] = float(entry.get())
                else:
                    stats[stat] = float(entry.get()) if entry.get() else 0.0  # Ensure a default value if the field is empty
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
            if stats.get('base_damage', 0) > 0 or stats.get('offensive_bonus', 0) > 0:
                offensive_level = calculate_offensive_level(stats['base_damage'], stats['offensive_bonus'], using_aggressive_style=True)
                selected_skill = self.prompt_offensive_skill(offensive_level)
                if selected_skill:
                    # Set the level for the selected skill
                    self.entries[selected_skill].delete(0, tk.END)
                    self.entries[selected_skill].insert(0, str(int(offensive_level)))  # Assuming you want the value as an integer
                    # Reset the offensive bonus and base damage entries
                    self.entries['offensive_bonus'].delete(0, tk.END)
                    self.entries['offensive_bonus'].insert(0, '0')
                    self.entries['base_damage'].delete(0, tk.END)
                    self.entries['base_damage'].insert(0, '0')

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

def calculate_offensive_level(base_damage, offensive_bonus, using_aggressive_style=False):
    # The invisible boost to the skill level when using aggressive style.
    aggressive_style_boost = 3 if using_aggressive_style else 1
    
    # Adjust the base_damage to account for the invisible boost by reverse-calculating it
    # assuming it's already part of the base_damage, then remove it to find the original skill level.
    adjusted_base_damage = base_damage - (aggressive_style_boost * ((offensive_bonus + 64)/640))

    # Now calculate the skill level without the invisible boost.
    skill_level_without_boost = (adjusted_base_damage - 0.5) / ((offensive_bonus + 64)/640)
    
    return skill_level_without_boost

def calculate_missing_levels(stats):
    desired_combat_level = stats['combat']
    
    # Unlock all stats, then remove locked ones and exclude offensive_bonus and base_damage
    unlocked_stats = [s for s in stats.keys() if s not in ['combat', 'offensive_bonus', 'base_damage']]
    for stat, lock_var in app.lock_vars.items():
        if lock_var.get() and stat in unlocked_stats:
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

class OffensiveSkillDialog(tk.Toplevel):
    def __init__(self, parent, offensive_level):
        super().__init__(parent)
        self.attributes('-topmost', True)  # This line sets the window to be always on top
        self.title("Choose Offensive Skill")
        self.selected_skill = None

        # Display the calculated offensive level
        ttk.Label(self, text=f"Calculated Offensive Level: {int(offensive_level)}").pack(pady=(10, 10))

        ttk.Button(self, text="Strength", command=lambda: self.select_skill("strength")).pack(fill=tk.BOTH)
        ttk.Button(self, text="Ranged", command=lambda: self.select_skill("ranged")).pack(fill=tk.BOTH)
        ttk.Button(self, text="Magic", command=lambda: self.select_skill("magic")).pack(fill=tk.BOTH)
        ttk.Button(self, text="Cancel", command=self.destroy).pack(fill=tk.BOTH)

        # Positioning the dialog near the parent window
        self.position_near_parent(parent)

    def select_skill(self, skill):
        self.selected_skill = skill
        self.destroy()

    def position_near_parent(self, parent):
        # Wait for the main window to update its geometry
        parent.update_idletasks()  # Ensures that the parent window's geometry is updated

        # Get the parent window's geometry, e.g., '600x400+240+120'
        parent_geometry = parent.winfo_geometry()
        
        # Parse the geometry string
        geometry_match = re.match(r'(\d+)x(\d+)([-+]\d+)([-+]\d+)', parent_geometry)
        if geometry_match:
            parent_x = int(geometry_match.group(3))
            parent_y = int(geometry_match.group(4))

            # Calculate dialog position
            dialog_x = parent_x + 100  # You might want to adjust this value
            dialog_y = parent_y + 100  # You might want to adjust this value

            # Set the dialog's position
            self.geometry(f'+{dialog_x}+{dialog_y}')
        else:
            print("Failed to parse parent geometry:", parent_geometry)

if __name__ == "__main__":
    app = CombatCalculator()
    app.mainloop()