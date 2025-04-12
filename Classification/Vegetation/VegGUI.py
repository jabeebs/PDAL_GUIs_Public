import tkinter as tk
from tkinter import filedialog, messagebox
import pdal
import json
import threading

class VegetationClassificationGUI:
    def __init__(self, master):
        self.master = master
        master.title("Vegetation Classification")

        # Input & Output File Selection
        tk.Label(master, text="Input File:").grid(row=0, column=0, sticky="w")
        self.input_entry = tk.Entry(master, width=50)
        self.input_entry.grid(row=0, column=1)
        tk.Button(master, text="Browse...", command=self.select_input_file).grid(row=0, column=2)

        tk.Label(master, text="Output File:").grid(row=1, column=0, sticky="w")
        self.output_entry = tk.Entry(master, width=50)
        self.output_entry.grid(row=1, column=1)
        tk.Button(master, text="Browse...", command=self.select_output_file).grid(row=1, column=2)

        # Run button
        tk.Button(master, text="Run Classification", command=self.run_classification).grid(row=2, column=0, columnspan=3, pady=10)

        # Status label
        self.status_label = tk.Label(master, text="", fg="blue")
        self.status_label.grid(row=3, column=0, columnspan=3)

    def select_input_file(self):
        filename = filedialog.askopenfilename(title="Select input file", filetypes=[("LAS/LAZ files", "*.las *.laz")])
        if filename:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)

    def select_output_file(self):
        filename = filedialog.asksaveasfilename(title="Select output file", defaultextension=".laz", filetypes=[("LAZ files", "*.laz")])
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)

    def run_classification(self):
        def classify():
            input_file = self.input_entry.get()
            output_file = self.output_entry.get()

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
                self.master.after(0, self.update_status, "Vegetation classification completed successfully.")
            except RuntimeError as e:
                self.master.after(0, self.update_status, f"An error occurred: {e}")

        self.update_status("Working...")
        threading.Thread(target=classify, daemon=True).start()

    def update_status(self, message):
        self.status_label.config(text=message)

# Launch the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = VegetationClassificationGUI(root)
    root.mainloop()
