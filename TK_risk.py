import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json

# Global variables to hold the current matplotlib figure and data
current_fig = None
current_df = None

def load_risk_mapping(filename='risk_config.json'):
    """Load risk mapping from a JSON file.
    If the file contains a dictionary with a "risk_mapping" key, use that;
    otherwise assume the file itself is a mapping. Returns a default mapping on error."""
    default_mapping = {"Critical Focus": 5, "Enhanced Focus": 3, "On Track": 1}
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        if isinstance(config, dict) and "risk_mapping" in config:
            return config["risk_mapping"]
        elif isinstance(config, dict):
            return config
        else:
            return default_mapping
    except Exception as e:
        print("Error loading risk mapping:", e)
        return default_mapping

def edit_risk_mapping():
    """Open a window that allows users to update category labels and scores."""
    edit_win = tk.Toplevel()
    edit_win.title("Edit Risk Mapping")
    
    # Load the current mapping
    current_mapping = load_risk_mapping()
    
    # Frame to hold our rows of entries
    rows_frame = tk.Frame(edit_win)
    rows_frame.pack(padx=10, pady=10)
    
    # Headers for the two columns
    tk.Label(rows_frame, text="Category Label").grid(row=0, column=0, padx=5)
    tk.Label(rows_frame, text="Score").grid(row=0, column=1, padx=5)
    
    # Lists to hold the entry widgets for later retrieval
    label_entries = []
    score_entries = []
    
    def add_row(label='', score=''):
        row = len(label_entries) + 1  # Adjust for header row
        lbl_entry = tk.Entry(rows_frame)
        lbl_entry.grid(row=row, column=0, padx=5, pady=2)
        lbl_entry.insert(0, label)
        scr_entry = tk.Entry(rows_frame)
        scr_entry.grid(row=row, column=1, padx=5, pady=2)
        scr_entry.insert(0, str(score))
        label_entries.append(lbl_entry)
        score_entries.append(scr_entry)
    
    # Populate the window with the current mapping
    for key, value in current_mapping.items():
        add_row(label=key, score=value)
    
    # Button to add an empty row for a new mapping
    def add_empty_row():
        add_row()
    
    add_row_button = tk.Button(edit_win, text="Add Category", command=add_empty_row)
    add_row_button.pack(pady=5)
    
    # Function to save the updated mapping to the JSON file
    def save_mapping():
        new_mapping = {}
        for lbl_entry, scr_entry in zip(label_entries, score_entries):
            label_text = lbl_entry.get().strip()
            score_text = scr_entry.get().strip()
            if label_text == "":
                continue  # Skip rows without a label
            try:
                score_value = float(score_text) if '.' in score_text else int(score_text)
            except ValueError:
                messagebox.showerror("Invalid Input", f"Score for '{label_text}' is not a valid number.")
                return
            new_mapping[label_text] = score_value
        
        try:
            with open("risk_config.json", "w") as f:
                # Save the mapping directly; alternatively, wrap it in a key if desired.
                json.dump(new_mapping, f, indent=4)
            messagebox.showinfo("Mapping Updated", "Risk mapping successfully updated!")
            edit_win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the mapping: {e}")
    
    save_button = tk.Button(edit_win, text="Save Mapping", command=save_mapping)
    save_button.pack(pady=5)

def load_data(filename):
    """Load compliance risk data from a CSV or Excel file."""
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filename)
        else:
            messagebox.showerror("Unsupported File", "Please upload a CSV or Excel file.")
            return None
        return df
    except Exception as e:
        messagebox.showerror("File Error", f"An error occurred while loading the file: {e}")
        return None

def convert_text_to_numeric(df):
    """Convert text-based risk ratings to numeric ratings using a configurable mapping."""
    risk_mapping = load_risk_mapping()  # load mapping from external JSON
    
    for col in ["Severity", "Implementation Period", "Impact"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()  # Remove extra spaces
            df[col] = df[col].map(risk_mapping)
            # If mapping fails, default to 1
            if df[col].isnull().any():
                df[col] = df[col].fillna(1)
    return df

def calculate_risk_score(df):
    """Calculate risk scores based on Severity, Implementation Period, and Impact."""
    df = convert_text_to_numeric(df)
    
    required_cols = {"Severity", "Implementation Period", "Impact"}
    if not required_cols.issubset(df.columns):
        messagebox.showerror("Missing Columns", "The required columns for risk calculation are missing.")
        return df

    df['Risk Score'] = df['Severity'] * df['Implementation Period'] * df['Impact']
    df['Risk Score'] = df['Risk Score'].astype(float)
    
    return df

def visualize_risk_bubble(df, parent_frame):
    """Generate and embed a risk assessment bubble chart in the given Tkinter frame."""
    global current_fig

    required_columns = {"Initiative", "Division", "Risk Score"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        messagebox.showerror("Missing Data", f"The following required columns are missing: {missing_columns}")
        return

    df["Initiative"] = df["Initiative"].astype(str).str.strip()
    df["Division"] = df["Division"].astype(str).str.strip()
    df = df.dropna(subset=["Risk Score"])

    agg_df = df.groupby(["Initiative", "Division"]).agg({"Risk Score": "mean"}).reset_index()

    divisions = sorted(agg_df["Division"].unique())
    initiatives = sorted(agg_df["Initiative"].unique())
    division_to_idx = {d: i for i, d in enumerate(divisions)}
    initiative_to_idx = {i: j for j, i in enumerate(initiatives)}
    agg_df["x"] = agg_df["Division"].map(division_to_idx)
    agg_df["y"] = agg_df["Initiative"].map(initiative_to_idx)

    sizes = agg_df["Risk Score"] * 100

    current_fig = plt.figure(figsize=(8, 6))
    scatter = plt.scatter(agg_df["x"], agg_df["y"], s=sizes, c=agg_df["Risk Score"],
                          cmap="plasma", alpha=0.8, edgecolors="black")
    plt.colorbar(scatter, label="Risk Score")
    plt.xticks(ticks=range(len(divisions)), labels=divisions, rotation=45)
    plt.yticks(ticks=range(len(initiatives)), labels=initiatives)
    plt.xlabel("Division")
    plt.ylabel("Initiative")
    plt.title("Compliance Risk Bubble Chart")
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(current_fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def visualize_risk_heatmap(df, parent_frame):
    """Generate and embed a risk assessment heatmap in the given Tkinter frame."""
    global current_fig

    required_columns = {"Initiative", "Division", "Risk Score"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        messagebox.showerror("Missing Data", f"The following required columns are missing: {missing_columns}")
        return

    df["Initiative"] = df["Initiative"].astype(str).str.strip()
    df["Division"] = df["Division"].astype(str).str.strip()
    df = df.dropna(subset=["Risk Score"])

    pivot_df = df.pivot_table(index="Initiative", columns="Division", values="Risk Score", aggfunc="mean")
    pivot_df = pivot_df.fillna(0)

    current_fig = plt.figure(figsize=(8, 6))
    ax = current_fig.add_subplot(111)
    sns.heatmap(pivot_df, annot=True, fmt=".1f", cmap="Reds", ax=ax)
    ax.set_title("Compliance Risk Heatmap")
    current_fig.tight_layout()

    canvas = FigureCanvasTkAgg(current_fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def visualize_risk_stacked_bar(df, parent_frame):
    """Generate and embed a risk assessment stacked bar chart in the given Tkinter frame."""
    global current_fig

    required_columns = {"Initiative", "Division", "Risk Score"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        messagebox.showerror("Missing Data", f"The following required columns are missing: {missing_columns}")
        return

    df["Initiative"] = df["Initiative"].astype(str).str.strip()
    df["Division"] = df["Division"].astype(str).str.strip()
    df = df.dropna(subset=["Risk Score"])

    pivot_df = df.pivot_table(index="Initiative", columns="Division", values="Risk Score", aggfunc="mean", fill_value=0)

    current_fig, ax = plt.subplots(figsize=(8, 6))
    pivot_df.plot(kind='bar', stacked=True, ax=ax, colormap="plasma")
    ax.set_title("Compliance Risk Stacked Bar Chart")
    ax.set_xlabel("Initiative")
    ax.set_ylabel("Risk Score")
    current_fig.tight_layout()

    canvas = FigureCanvasTkAgg(current_fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def save_chart():
    """Save the currently displayed chart to a file."""
    global current_fig
    if current_fig is None:
        messagebox.showwarning("No Chart", "There is no chart to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")]
    )
    if file_path:
        try:
            current_fig.savefig(file_path, dpi=300)
            messagebox.showinfo("Chart Saved", f"Chart successfully saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred while saving the chart: {e}")

def draw_chart(chart_frame, chart_type):
    """Draw the selected chart type using the currently loaded data."""
    global current_df
    if current_df is None:
        messagebox.showwarning("No Data", "No data loaded. Please load a file first.")
        return

    # Clear the chart frame before drawing the new chart
    for widget in chart_frame.winfo_children():
        widget.destroy()

    if chart_type.get() == "Bubble Chart":
        visualize_risk_bubble(current_df, chart_frame)
    elif chart_type.get() == "Heatmap":
        visualize_risk_heatmap(current_df, chart_frame)
    elif chart_type.get() == "Stacked Bar Chart":
        visualize_risk_stacked_bar(current_df, chart_frame)
    else:
        messagebox.showerror("Unknown Chart", f"Chart type '{chart_type.get()}' is not supported.")

def on_load_file(chart_frame, chart_type):
    """Handler for file loading: loads data, calculates risk scores, and draws the selected chart."""
    global current_df
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
    if file_path:
        df = load_data(file_path)
        if df is not None:
            current_df = calculate_risk_score(df)
            draw_chart(chart_frame, chart_type)

def main():
    root = tk.Tk()
    root.title("Risk Assessment Dashboard")
    root.geometry("900x700")
    
    # Top frame for controls
    top_frame = tk.Frame(root)
    top_frame.pack(pady=10)
    
    chart_type = tk.StringVar()
    chart_type.set("Bubble Chart")  # default selection
    chart_type_menu = tk.OptionMenu(top_frame, chart_type, "Bubble Chart", "Heatmap", "Stacked Bar Chart")
    chart_type_menu.pack(side=tk.LEFT, padx=5)
    
    load_button = tk.Button(top_frame, text="Load Data File",
                            command=lambda: on_load_file(chart_frame, chart_type))
    load_button.pack(side=tk.LEFT, padx=5)
    
    refresh_button = tk.Button(top_frame, text="Refresh Chart",
                               command=lambda: draw_chart(chart_frame, chart_type))
    refresh_button.pack(side=tk.LEFT, padx=5)
    
    # Button to open the risk mapping editor
    edit_mapping_button = tk.Button(top_frame, text="Edit Risk Mapping", command=edit_risk_mapping)
    edit_mapping_button.pack(side=tk.LEFT, padx=5)
    
    save_button = tk.Button(top_frame, text="Save Chart", command=save_chart)
    save_button.pack(side=tk.LEFT, padx=5)
    
    chart_frame = tk.Frame(root)
    chart_frame.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    main()
