import tkinter as tk
from tkinter import filedialog, messagebox
import pdal
import json
import os
import threading

class VegetationClassificationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Vegetation Classification")

        config = [
            ("Input File:", self.select_input_file, None),
            ("Output File:", self.select_output_file, None)
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

        tk.Button(master, text="Run Vegetation Classification", command=self.run_classification).grid(row=len(config), column=0, columnspan=3)

        self.status_label = tk.Label(master, text="", fg="blue")
        self.status_label.grid(row=len(config)+1, column=0, columnspan=3, pady=(5, 0))

    def select_input_file(self):
        filename = filedialog.askopenfilename(title="Select input file", filetypes=(("LAS/LAZ files", "*.las *.laz"), ("All files", "*.*")))
        if filename:
            self.entries['input_file'].delete(0, tk.END)
            self.entries['input_file'].insert(0, filename)

    def select_output_file(self):
        filename = filedialog.asksaveasfilename(title="Select output file", defaultextension=".laz", filetypes=(("LAZ files", "*.laz"), ("All files", "*.*")))
        if filename:
            self.entries['output_file'].delete(0, tk.END)
            self.entries['output_file'].insert(0, filename)

    def run_classification(self):
        def classify():
            input_file = self.entries['input_file'].get()
            output_file = self.entries['output_file'].get()

            pipeline_json = {
                "pipeline": [
                    {"type": "readers.las", "filename": input_file},
                    {"type": "filters.hag_nn"},
                    {"type": "filters.covariancefeatures", "knn": 8},
                    {"type": "filters.estimaterank"},
                    {"type": "filters.normal"},
                    {
                        "type": "filters.assign",
                        "value": [
                            "Classification = 5 WHERE ((Classification == 1) && "
                            "(HeightAboveGround > 2) && (HeightAboveGround < 45) && "
                            "(Planarity < 0.85) && (Linearity < 0.9) && "
                            "(Verticality > 0.25) && (ReturnNumber >= 1) && "
                            "(Rank >= 2) && (Curvature > 0.001))"
                        ]
                    },
                    {"type": "writers.las", "filename": output_file}
                ]
            }

            pipeline = pdal.Pipeline(json.dumps(pipeline_json))
            try:
                pipeline.execute()
                self.master.after(0, self.clear_status)
                self.master.after(0, lambda: messagebox.showinfo("Processing", "Vegetation classification completed successfully!"))
            except RuntimeError as e:
                self.master.after(0, self.clear_status)
                self.master.after(0, lambda: messagebox.showerror("Processing", f"An error occurred: {e}"))

        self.status_label.config(text="Working...")
        threading.Thread(target=classify, daemon=True).start()

    def clear_status(self):
        self.status_label.config(text="")

# Launch the GUI
root = tk.Tk()
app = VegetationClassificationGUI(root)
root.mainloop()
