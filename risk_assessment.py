import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import io
from matplotlib.colors import LinearSegmentedColormap

# Corporate color scheme
NAVY_BLUE = "#001f3f"
GOLD = "#FFD700"
YELLOW = "#FFFF00"
ORANGE = "#FFA500"

def get_corporate_cmap():
    corporate_colors = [NAVY_BLUE, GOLD, YELLOW, ORANGE]
    return LinearSegmentedColormap.from_list("corp_map", corporate_colors)

def load_risk_mapping(filename='risk_config.json'):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_risk_mapping(mapping, filename='risk_config.json'):
    with open(filename, 'w') as f:
        json.dump(mapping, f, indent=4)

def auto_generate_risk_mapping(df):
    mapping = {}
    predefined_scores = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Minimal": 1}
    for col in df.columns:
        unique_values = df[col].dropna().unique().tolist()
        mapping[col] = {val: predefined_scores.get(str(val), 1) for val in unique_values}
    return mapping

def download_risk_mapping(risk_mapping):
    risk_json = json.dumps(risk_mapping, indent=4)
    return io.BytesIO(risk_json.encode())

def column_mapping_interface(df):
    st.sidebar.subheader("Map Your Columns")
    columns = df.columns.tolist()
    mappings = {}
    with st.sidebar.expander("Column Mappings"):
        mappings["Severity"] = st.selectbox("Select Severity Column", columns)
        mappings["Implementation Period"] = st.selectbox("Select Implementation Period Column", columns)
        mappings["Impact"] = st.selectbox("Select Impact Column", columns)
        mappings["Initiative"] = st.selectbox("Select Initiative Column", columns)
        mappings["Division"] = st.selectbox("Select Division Column", columns)
    
    ignore_columns = st.sidebar.multiselect("Select columns to ignore in calculations", columns, default=[])
    return mappings, ignore_columns

def customize_risk_mapping(df):
    st.sidebar.subheader("Customize Risk Mapping")
    risk_mapping = load_risk_mapping() or auto_generate_risk_mapping(df)
    updated_mapping = {}
    with st.sidebar.expander("Modify Risk Mapping"):
        for col in df.columns:
            st.write(f"### {col} Mapping")
            col_mapping = risk_mapping.get(col, {})
            new_mapping = {val: st.number_input(f"{col}: {val}", value=score, step=1) for val, score in col_mapping.items()}
            updated_mapping[col] = new_mapping
        if st.button("Save Risk Mapping"):
            save_risk_mapping(updated_mapping)
            st.success("Risk mapping updated successfully!")
    st.sidebar.download_button("Download Risk Mapping", download_risk_mapping(updated_mapping), "risk_config.json", "application/json")

def convert_text_to_numeric(df, mappings, ignore_columns):
    risk_mapping = load_risk_mapping()
    for col in ["Severity", "Implementation Period", "Impact"]:
        mapped_col = mappings[col]
        if mapped_col in df.columns and mapped_col not in ignore_columns:
            df[mapped_col] = df[mapped_col].astype(str).str.strip().map(risk_mapping.get(mapped_col, {})).fillna(1)
    return df

def calculate_risk_score(df, mappings, ignore_columns):
    df = convert_text_to_numeric(df, mappings, ignore_columns)
    df['Risk Score'] = df[mappings['Severity']] * df[mappings['Implementation Period']] * df[mappings['Impact']]
    return df

def visualize_risk_chart(df, chart_type, mappings):
    custom_cmap = get_corporate_cmap()
    st.write("### Risk Visualization")
    plt.figure(figsize=(12, 8))
    if chart_type == "Bubble Chart":
        scatter = plt.scatter(df[mappings["Division"]], df[mappings["Initiative"]],
                              s=df["Risk Score"] * 100, c=df["Risk Score"], cmap=custom_cmap, alpha=0.8, edgecolors="black")
        plt.colorbar(scatter, label="Risk Score")
        plt.xticks(rotation=45)
        plt.xlabel("Division")
        plt.ylabel("Initiative")
        plt.title("Risk Bubble Chart")
    elif chart_type == "Heatmap":
        pivot_df = df.pivot_table(index=mappings["Initiative"], columns=mappings["Division"], values="Risk Score", aggfunc="mean").fillna(0)
        sns.heatmap(pivot_df, annot=True, cmap=custom_cmap, linewidths=0.5, linecolor='black', cbar_kws={"label": "Risk Score"})
        plt.title("Risk Heatmap")
    elif chart_type == "Stacked Bar Chart":
        pivot_df = df.pivot_table(index=mappings["Initiative"], columns=mappings["Division"], values="Risk Score", aggfunc="mean", fill_value=0)
        pivot_df.plot(kind='bar', stacked=True, colormap=custom_cmap, figsize=(12, 8))
        plt.xticks(rotation=45)
        plt.xlabel("Initiative")
        plt.ylabel("Risk Score")
        plt.title("Risk Stacked Bar Chart")
    st.pyplot(plt)

def main():
    st.title("Enhanced Risk Assessment Dashboard")
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        mappings, ignore_columns = column_mapping_interface(df)
        customize_risk_mapping(df)
        df = calculate_risk_score(df, mappings, ignore_columns)
        st.write("### Processed Data")
        st.dataframe(df)
        chart_type = st.selectbox("Select Chart Type", ["Bubble Chart", "Heatmap", "Stacked Bar Chart"])
        if st.button("Generate Chart"):
            visualize_risk_chart(df, chart_type, mappings)
if __name__ == "__main__":
    main()