import tkinter as tk
from tkinter import filedialog, messagebox
import pdal
import json
import os
import threading

class PowerlineClassificationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Powerline Classification")

        config = [
            ("Input File:", self.select_input_file, None),
            ("Output File:", self.select_output_file, None),
            ("Height Above Ground:", None, "10"),
            ("Linearity:", None, "0.75")
        ]

        self.entries = {}
        for idx, (label, action, default_val) in enumerate(config):
            tk.Label(master, text=label).grid(row=idx, column=0, sticky="w")
            entry = tk.Entry(master, width=50 if action else 10)
            entry.grid(row=idx, column=1)
            if default_val is not None:
                entry.insert(0, default_val)
            if action:
                tk.Button(master, text="Browse...", command=action).grid(row=idx, column=2)
            self.entries[label[:-1].lower().replace(" ", "_")] = entry

        tk.Button(master, text="Run Classification", command=self.run_classification).grid(row=len(config), column=0, columnspan=3)

        # Status label (initially empty)
        self.status_label = tk.Label(master, text="", fg="blue")
        self.status_label.grid(row=len(config)+1, column=0, columnspan=3, pady=(5, 0))

    def select_input_file(self):
        filename = filedialog.askopenfilename(title="Select input file", filetypes=(("LAZ files", "*.laz"), ("All files", "*.*")))
        if filename:
            self.entries['input_file'].delete(0, tk.END)
            self.entries['input_file'].insert(0, filename)

    def select_output_file(self):
        filename = filedialog.asksaveasfilename(title="Select output file", filetypes=(("LAZ files", "*.laz"), ("All files", "*.*")), defaultextension=".laz")
        if filename:
            self.entries['output_file'].delete(0, tk.END)
            self.entries['output_file'].insert(0, filename)

    def run_classification(self):
        def classify():
            input_file = self.entries['input_file'].get()
            output_file = self.entries['output_file'].get()
            height_thresh = float(self.entries['height_above_ground'].get())
            linearity_thresh = float(self.entries['linearity'].get())

            assignment_expr = (
                f"Classification = 13 WHERE ((HeightAboveGround > {height_thresh}) && "
                f"(ReturnNumber == 1) && (Linearity > {linearity_thresh}) && (Classification != 2))"
            )

            pipeline_json = {
                "pipeline": [
                    {"type": "readers.las", "filename": input_file},
                    {"type": "filters.smrf", "ignore": "Classification[7:7]"},
                    {"type": "filters.hag_nn"},
                    {"type": "filters.covariancefeatures", "feature_set": "Linearity"},
                    {
                        "type": "filters.assign",
                        "value": [assignment_expr]
                    },
                    {"type": "writers.las", "filename": output_file}
                ]
            }

            pipeline = pdal.Pipeline(json.dumps(pipeline_json))
            try:
                pipeline.execute()
                self.master.after(0, self.clear_status)
                self.master.after(0, lambda: messagebox.showinfo("Processing", "Powerline classification completed successfully!"))
            except RuntimeError as e:
                self.master.after(0, self.clear_status)
                self.master.after(0, lambda: messagebox.showerror("Processing", f"An error occurred: {e}"))

        self.status_label.config(text="Working...")
        threading.Thread(target=classify, daemon=True).start()

    def clear_status(self):
        self.status_label.config(text="")

# Launch the GUI
root = tk.Tk()
app = PowerlineClassificationGUI(root)
root.mainloop()
