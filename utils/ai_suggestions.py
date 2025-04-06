import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from openai import OpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def generate_column_cleaning_suggestions(df, column_name, column_type):
    """Generate AI suggestions for cleaning a specific column."""
    if df is None or df.empty or column_name not in df.columns:
        return []
    
    # Extract column data and statistics
    column_data = df[column_name]
    
    # Basic statistics
    missing_count = column_data.isna().sum()
    missing_percent = (missing_count / len(df) * 100)
    unique_values = column_data.nunique()
    
    # Generate a sample of values (avoiding leaking too much data)
    sample_size = min(5, len(column_data.dropna()))
    sample_values = column_data.dropna().sample(sample_size).tolist()
    
    # Prepare the context for OpenAI
    prompt = f"""
    I need cleaning recommendations for a data column with these properties:
    - Column name: {column_name}
    - Data type: {column_type}
    - Missing values: {missing_count} ({missing_percent:.2f}%)
    - Unique values: {unique_values}
    - Sample values: {', '.join([str(v) for v in sample_values])}
    
    Provide JSON with actionable cleaning recommendations. Each recommendation should include:
    - operation: name of the operation (e.g., 'impute_missing', 'normalize', 'remove_outliers')
    - description: human-readable explanation of what this operation does
    - rationale: why this operation would benefit the data
    - code_action: the transformation code reference (will be linked to actual transformation functions)
    
    Return a JSON array of recommendations like this:
    [
        {
            "operation": "string",
            "description": "string",
            "rationale": "string",
            "code_action": "string"
        }
    ]
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data cleaning expert. Provide specific, actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('recommendations', []) if isinstance(result, dict) and 'recommendations' in result else result
    except Exception as e:
        st.error(f"Error generating cleaning suggestions: {str(e)}")
        return []

def generate_dataset_insights(df):
    """Generate AI insights about the entire dataset."""
    if df is None or df.empty:
        return []
    
    # Prepare summary statistics
    summary = {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'missing_values': df.isna().sum().to_dict(),
        'numeric_columns': df.select_dtypes(include=['number']).columns.tolist(),
        'categorical_columns': df.select_dtypes(include=['object', 'category']).columns.tolist(),
        'datetime_columns': df.select_dtypes(include=['datetime']).columns.tolist()
    }
    
    # Calculate correlations for numeric columns
    if len(summary['numeric_columns']) > 1:
        correlation_matrix = df[summary['numeric_columns']].corr().round(2).to_dict()
        summary['correlations'] = correlation_matrix
    
    # Prepare the context for OpenAI
    prompt = f"""
    Analyze this dataset summary and provide meaningful insights:
    {json.dumps(summary, default=str)}
    
    Provide JSON with actionable insights. Each insight should include:
    - type: the type of insight (e.g., 'correlation', 'missing_data', 'distribution', 'trend')
    - title: a concise headline summarizing the insight
    - description: detailed explanation of the insight with specific values/details
    - importance: a value from 1-5 indicating how important/significant this insight is
    - recommended_action: what action could be taken based on this insight
    
    Return a JSON array of insights like this:
    [
        {{
            "type": "string",
            "title": "string",
            "description": "string",
            "importance": number,
            "recommended_action": "string"
        }}
    ]
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data insights expert. Provide specific, valuable insights from data."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1500
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('insights', []) if isinstance(result, dict) and 'insights' in result else result
    except Exception as e:
        st.error(f"Error generating dataset insights: {str(e)}")
        return []

def suggest_visualizations(df):
    """Suggest appropriate visualizations based on data types."""
    if df is None or df.empty:
        return []
    
    # Identify column types
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_columns = df.select_dtypes(include=['datetime']).columns.tolist()
    
    # Generate sample column combinations for visualizations
    sample_num_cols = numeric_columns[:3] if len(numeric_columns) > 3 else numeric_columns
    sample_cat_cols = categorical_columns[:3] if len(categorical_columns) > 3 else categorical_columns
    sample_date_cols = datetime_columns[:2] if len(datetime_columns) > 2 else datetime_columns
    
    # Prepare dataset summary
    summary = {
        'shape': df.shape,
        'numeric_columns': numeric_columns,
        'categorical_columns': categorical_columns,
        'datetime_columns': datetime_columns,
        'sample_numeric': sample_num_cols,
        'sample_categorical': sample_cat_cols,
        'sample_datetime': sample_date_cols
    }
    
    # Prepare the context for OpenAI
    prompt = f"""
    Suggest appropriate visualizations for this dataset:
    {json.dumps(summary, default=str)}
    
    Provide JSON with visualization recommendations. Each recommendation should include:
    - chart_type: type of visualization (e.g., 'histogram', 'scatter_plot', 'bar_chart')
    - title: suggested title for the visualization
    - columns: list of columns to use in this visualization
    - description: why this visualization would be useful
    - plotly_fig_type: the Plotly figure type to use (e.g., 'px.histogram', 'px.scatter')
    
    Only suggest visualizations that make sense for the data types. Prioritize visualizations that would reveal insights.
    
    Return a JSON array of visualization suggestions like this:
    [
        {{
            "chart_type": "string",
            "title": "string",
            "columns": ["string"],
            "description": "string",
            "plotly_fig_type": "string"
        }}
    ]
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data visualization expert. Suggest appropriate and insightful visualizations."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1200
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('visualizations', []) if isinstance(result, dict) and 'visualizations' in result else result
    except Exception as e:
        st.error(f"Error generating visualization suggestions: {str(e)}")
        return []

def answer_data_question(df, question):
    """Use AI to answer a natural language question about the data."""
    if df is None or df.empty or not question:
        return {"answer": "No data available or question not provided."}
    
    # Prepare a summary of the dataset
    columns_info = {}
    for column in df.columns:
        dtype = str(df[column].dtype)
        sample = df[column].dropna().sample(min(3, len(df[column].dropna()))).tolist()
        unique_count = df[column].nunique()
        missing_count = df[column].isna().sum()
        
        columns_info[column] = {
            "type": dtype,
            "sample_values": sample,
            "unique_count": unique_count,
            "missing_count": missing_count
        }
    
    dataset_summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "columns_info": columns_info
    }
    
    # Prepare the context for OpenAI
    prompt = f"""
    Given this dataset:
    {json.dumps(dataset_summary, default=str)}
    
    Answer this question: "{question}"
    
    Provide a clear, concise answer with relevant statistics or facts from the data.
    If the question cannot be answered with the available data, explain why.
    If analysis is needed to answer the question, describe what analysis would be performed.
    
    Return JSON with this structure:
    {{
        "answer": "string with detailed answer",
        "confidence": number between 0 and 1,
        "relevant_columns": ["list of columns relevant to this question"],
        "suggested_visualization": "string describing a visualization to answer this question" (optional)
    }}
    """
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a data analyst expert. Answer questions about datasets accurately and helpfully."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error answering data question: {str(e)}")
        return {"answer": f"Error processing question: {str(e)}", "confidence": 0, "relevant_columns": []}
