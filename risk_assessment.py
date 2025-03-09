import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

def load_data(uploaded_file):
    """Load compliance risk data from a CSV or Excel file."""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Unsupported file format. Use CSV or Excel.")
        return None
    return df

def convert_text_to_numeric(df):
    """Convert text-based risk ratings to numeric ratings and handle errors."""
    risk_mapping = {
        "Critical Focus": 5,
        "Enhanced Focus": 3,
        "On Track": 1
    }
    
    for col in ["Severity", "Implementation Period", "Impact"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()  # Remove spaces before mapping
            df[col] = df[col].map(risk_mapping)
            
            # Handle unmapped values by defaulting to 1.
            if df[col].isnull().any():
                missing_values = df.loc[df[col].isnull(), col].unique()
                st.warning(f"Warning: Some values in {col} could not be mapped: {missing_values}. Defaulting to 1.")
                df[col] = df[col].fillna(1)
    
    return df

def calculate_risk_score(df):
    """Calculate risk scores based on severity, implementation period, and impact."""
    df = convert_text_to_numeric(df)
    
    # Check that all required columns exist
    required = {"Severity", "Implementation Period", "Impact"}
    if not required.issubset(df.columns):
        st.error("Required columns for risk calculation are missing.")
        return df
    
    df['Risk Score'] = df['Severity'] * df['Implementation Period'] * df['Impact']
    df['Risk Score'] = df['Risk Score'].astype(float)
    
    if df['Risk Score'].isnull().any():
        st.error("Error: Some Risk Scores are NaN after calculation! Check input data.")
    
    return df

def visualize_risk_bubble(df):
    """Generate a risk assessment bubble chart."""
    # Ensure required columns exist and clean data
    required_columns = {"Initiative", "Division", "Risk Score"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        st.error(f"Error: Missing columns in dataset: {missing_columns}")
        return

    df["Initiative"] = df["Initiative"].astype(str).str.strip()
    df["Division"] = df["Division"].astype(str).str.strip()
    df = df.dropna(subset=["Risk Score"])

    # Aggregate data if multiple rows exist for the same Initiative/Division pair
    agg_df = df.groupby(["Initiative", "Division"]).agg({"Risk Score": "mean"}).reset_index()

    # Create mappings for categorical x (Division) and y (Initiative) axes
    divisions = sorted(agg_df["Division"].unique())
    initiatives = sorted(agg_df["Initiative"].unique())
    division_to_idx = {d: i for i, d in enumerate(divisions)}
    initiative_to_idx = {i: j for j, i in enumerate(initiatives)}

    agg_df["x"] = agg_df["Division"].map(division_to_idx)
    agg_df["y"] = agg_df["Initiative"].map(initiative_to_idx)

    # Determine bubble sizes (adjust the multiplier as needed)
    sizes = agg_df["Risk Score"] * 100

    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(agg_df["x"], agg_df["y"], s=sizes, c=agg_df["Risk Score"],
                          cmap="plasma", alpha=0.8, edgecolors="black")
    plt.colorbar(scatter, label="Risk Score")
    plt.xticks(ticks=range(len(divisions)), labels=divisions)
    plt.yticks(ticks=range(len(initiatives)), labels=initiatives)
    plt.xlabel("Division")
    plt.ylabel("Initiative")
    plt.title("Compliance Risk Bubble Chart")
    st.pyplot(plt)
    plt.close()

def main():
    st.title("Risk Assessment Dashboard")
    st.write("Upload your compliance risk data (CSV or Excel)")
    
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        if df is not None:
            df = calculate_risk_score(df)
            st.write("### Risk Data Table")
            st.dataframe(df)
            st.write("### Risk Bubble Chart")
            visualize_risk_bubble(df)

if __name__ == "__main__":
    main()
