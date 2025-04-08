import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from utils.ai_providers import get_ai_manager

# Get AI manager instance
ai_manager = get_ai_manager()

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
    
    Return a JSON array of recommendations with this structure:
    [
        {{
            "operation": "string",
            "description": "string",
            "rationale": "string",
            "code_action": "string"
        }}
    ]
    """
    
    try:
        # Use the AI manager to generate the completion
        system_message = "You are a data cleaning expert. Provide specific, actionable recommendations."
        result = ai_manager.generate_completion(
            prompt=prompt, 
            system_message=system_message,
            json_response=True,
            max_tokens=1000
        )
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
        # Use the AI manager to generate the completion
        system_message = """You are a data insights expert. Provide specific, valuable insights from data.
Return your response as a JSON array of insight objects with exactly these fields for each insight:
- category: one of "general", "statistical", "pattern", or "anomaly"
- title: a concise headline summarizing the insight
- description: detailed explanation of the insight with specific values/details
- importance: a value from 1-5 indicating importance
- recommended_action: what action could be taken based on this insight
- visualization: (optional) object with chart_type and columns fields if a visualization would help

Example format:
{
  "insights": [
    {
      "category": "general",
      "title": "Dataset Overview",
      "description": "The dataset contains 1000 rows and 5 columns with complete data.",
      "importance": 3,
      "recommended_action": "No action needed, data is complete."
    },
    {
      "category": "statistical",
      "title": "Strong Correlation Between X and Y",
      "description": "Variables X and Y show a strong positive correlation of 0.85.",
      "importance": 4,
      "recommended_action": "Consider using X as a predictor for Y in models.",
      "visualization": {
        "chart_type": "scatter_plot",
        "columns": ["X", "Y"]
      }
    }
  ]
}
"""
        result = ai_manager.generate_completion(
            prompt=prompt, 
            system_message=system_message,
            json_response=True,
            max_tokens=1500
        )
        
        # Check for different possible response formats and normalize them
        if isinstance(result, str):
            # If it's a string, try to parse it as JSON
            try:
                result = json.loads(result)
            except Exception as e:
                st.error(f"Error parsing insights JSON: {str(e)}")
                return []
                
        if isinstance(result, dict):
            # Check for common response structures
            if 'insights' in result:
                insights = result['insights']
                # Make sure it's a list
                if not isinstance(insights, list):
                    insights = [insights] if insights else []
                return insights
            # If it has expected insight fields, it might be a single insight
            elif all(key in result for key in ['title', 'description']):
                # Add category if missing
                if 'category' not in result:
                    result['category'] = 'general'
                return [result]
            else:
                # Look for any array in the result that might contain insights
                for key, value in result.items():
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict) and 'title' in value[0]:
                            return value
                # If no suitable insights found, return an empty list
                return []
        elif isinstance(result, list):
            # It's already a list, make sure items have required fields
            normalized_insights = []
            for item in result:
                if isinstance(item, dict) and 'title' in item and 'description' in item:
                    # Add category if missing
                    if 'category' not in item:
                        item['category'] = 'general'
                    normalized_insights.append(item)
            return normalized_insights
        else:
            # If it's something unexpected, return empty list
            return []
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
        # Use the AI manager to generate the completion
        system_message = """You are a data visualization expert. Suggest appropriate and insightful visualizations.
Return your response in a properly formatted JSON array of visualization objects with the exact structure and fields requested.
Make sure each visualization has chart_type, title, columns, description, and plotly_fig_type fields.
The chart_type should be one of: histogram, scatter_plot, bar_chart, line_chart, pie_chart, box_plot, heatmap, correlation_heatmap, pair_plot, or similar.
The columns field must be an array of column names, even if it's just one column.

IMPORTANT: For JSON formatting, always use double quotes for properties and string values, and include commas between properties.
Format properly as:
[
  {
    "chart_type": "scatter_plot",
    "title": "Units vs. Price",
    "columns": ["Units", "Price"],
    "description": "This scatter plot helps understand the relationship between units and price.",
    "plotly_fig_type": "px.scatter"
  },
  {
    "chart_type": "histogram",
    "title": "Distribution of Revenue",
    "columns": ["Revenue"],
    "description": "Shows the distribution of revenue values.",
    "plotly_fig_type": "px.histogram"
  }
]
"""
        result = ai_manager.generate_completion(
            prompt=prompt, 
            system_message=system_message,
            json_response=True,
            max_tokens=1200
        )
        
        # Check for different possible response formats and normalize them
        if isinstance(result, str):
            # If it's a string, try to parse it as JSON
            try:
                result = json.loads(result)
            except Exception as e:
                st.error(f"Error parsing visualization JSON: {str(e)}")
                return []
                
        if isinstance(result, dict):
            # Check for common response structures
            if 'visualizations' in result:
                return result['visualizations']
            elif 'visualization_recommendations' in result:
                return result['visualization_recommendations']
            elif 'recommendations' in result:
                return result['recommendations']
            elif 'chart_type' in result:
                # It's a single visualization
                return [result]
            else:
                # Look for any array that might contain visualization objects
                for key, value in result.items():
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict) and ('chart_type' in value[0] or 'plotly_fig_type' in value[0]):
                            return value
                # If no suitable array found, wrap the entire dict
                return [result]
        elif isinstance(result, list):
            # If it's already a list, return it if it has valid items
            if len(result) > 0 and isinstance(result[0], dict):
                return result
            else:
                # Empty list or not a list of dicts
                return []
        else:
            # If it's something unexpected, return an empty list
            return []
    except Exception as e:
        st.error(f"Error generating visualization suggestions: {str(e)}")
        return []

def answer_data_question(df, question):
    """Use AI to answer a natural language question about the data."""
    if df is None or df.empty or not question:
        return {"text": "No data available or question not provided."}
    
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
    
    # Prepare the context for AI
    prompt = f"""
    Given this dataset:
    {json.dumps(dataset_summary, default=str)}
    
    Answer this question: "{question}"
    
    Provide a clear, concise answer with relevant statistics or facts from the data.
    If the question cannot be answered with the available data, explain why.
    If analysis is needed to answer the question, describe what analysis would be performed.
    
    Return JSON with this structure:
    {{
        "text": "string with detailed answer",
        "confidence": number between 0 and 1,
        "relevant_columns": ["list of columns relevant to this question"],
        "visualization": {{
            "chart_type": "appropriate chart type (e.g., bar_chart, scatter_plot, histogram)",
            "title": "suggested visualization title",
            "description": "what this visualization shows",
            "columns": ["columns to include in the visualization"]
        }} (optional)
    }}
    """
    
    try:
        # Use the AI manager to generate the completion
        system_message = """You are a data analyst expert. Answer questions about datasets accurately and helpfully.
If a visualization would help illustrate your answer, include the visualization object in your response.
Make sure your response is properly formatted JSON with the exact structure requested.
The visualization.chart_type should be one of: bar_chart, line_chart, scatter_plot, histogram, box_plot, pie_chart, or correlation_heatmap.
The visualization.columns must be an array of actual column names from the dataset, even if it's just one column.
"""
        result = ai_manager.generate_completion(
            prompt=prompt, 
            system_message=system_message,
            json_response=True,
            max_tokens=1200
        )
        
        # Check if result is a string (raw JSON) and parse it if needed
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception as e:
                st.error(f"Error parsing answer JSON: {str(e)}")
                return {"text": f"Error processing response: {str(e)}"}
        
        # Ensure we have the expected keys and normalize the response
        required_keys = ['text', 'confidence', 'relevant_columns']
        if isinstance(result, dict):
            # Convert 'answer' to 'text' if needed for consistency
            if 'answer' in result and 'text' not in result:
                result['text'] = result['answer']
            
            # Add default values for any missing required keys
            for key in required_keys:
                if key not in result:
                    if key == 'text':
                        result[key] = "Unable to determine answer from the data."
                    elif key == 'confidence':
                        result[key] = 0.0
                    elif key == 'relevant_columns':
                        result[key] = []
            
            # Ensure confidence is within valid range
            if 'confidence' in result:
                try:
                    confidence = float(result['confidence'])
                    result['confidence'] = max(0.0, min(1.0, confidence))
                except:
                    result['confidence'] = 0.0
            
            # Normalize visualization structure
            if 'suggested_visualization' in result and 'visualization' not in result:
                if isinstance(result['suggested_visualization'], str):
                    # It's just a text description, create a simple visualization object
                    viz_desc = result['suggested_visualization']
                    result['visualization'] = {
                        "chart_type": "bar_chart",  # Default type
                        "title": "Suggested Visualization",
                        "description": viz_desc,
                        "columns": result.get('relevant_columns', [])[:2]  # Use up to 2 relevant columns 
                    }
                elif isinstance(result['suggested_visualization'], dict):
                    # It's already an object, just rename the key
                    result['visualization'] = result['suggested_visualization']
            
            return result
        else:
            # Return a default response if we didn't get a dict
            return {
                "text": "Error: Unexpected response format from AI service.",
                "confidence": 0,
                "relevant_columns": []
            }
    except Exception as e:
        st.error(f"Error answering data question: {str(e)}")
        return {"text": f"Error processing question: {str(e)}", "confidence": 0, "relevant_columns": []}
