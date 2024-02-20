# modified code from original source : https://www.mlq.ai/csv-assistant-langchain/

import streamlit as st
import pandas as pd
import json
import openai
import os
import re
import matplotlib.pyplot as plt
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType

def csv_agent_func(file_path, user_message):
    """Run the CSV agent with the given file path and user message."""
    agent = create_csv_agent(
        ChatOpenAI(temperature=0, model="gpt-3.5-turbo-1106", openai_api_key=os.environ["OPENAI_API_KEY"]),
        file_path, 
        verbose=True,
        agent_type=AgentType.OPENAI_FUNCTIONS,
    )

    try:        
        response = agent.run(user_message)
        return response
    except Exception as e:
        st.write(f"Error when running user message: {e}")
        return None


def display_content_from_json(json_response):
    """
    Display content to Streamlit based on the structure of the provided JSON.
    Something new
    """
    
    # Check if the response has plain text.
    if "answer" in json_response:
        st.write(json_response["answer"])

    # Check if the response has a bar chart.
    if "bar" in json_response:
        data = json_response["bar"]
        df = pd.DataFrame(data)
        df.set_index("columns", inplace=True)
        st.bar_chart(df)

    # Check if the response has a table.
    if "table" in json_response:
        data = json_response["table"]
        df = pd.DataFrame(data["data"], columns=data["columns"])
        st.table(df)

def extract_code_from_response(response):
    """Extracts Python code from a string response."""
    # Use a regex pattern to match content between triple backticks
    code_pattern = r"```python(.*?)```"
    match = re.search(code_pattern, response, re.DOTALL)
    
    if match:
        # Extract the matched code and strip any leading/trailing whitespaces
        return match.group(1).strip()

    return None


def csv_analyzer_app():
    """Main Streamlit application for CSV analysis."""

    st.title('CSV Assistant')
    st.write('Please upload your CSV file and enter your query below:')
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.write(file_details)
        
        # Save the uploaded file to disk
        file_path = os.path.join("/tmp", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        df = pd.read_csv(file_path, on_bad_lines='skip', low_memory=False, dtype={0:str,2:str,5:str,6:str})
        st.dataframe(df)
        
        user_input = st.text_input("Your query")
        print(user_input)
        if st.button('Run'):
            response = csv_agent_func(file_path, user_input)
            
            # Extracting code from the response
            code_to_execute = extract_code_from_response(response)
            
            if code_to_execute:
                try:
                    # Making df available for execution in the context
                    exec(code_to_execute, globals(), {"df": df, "plt": plt})
                    fig = plt.gcf()  # Get current figure
                    st.pyplot(fig)  # Display using Streamlit
                except Exception as e:
                    st.write(f"Error executing code: {e}")
            else:
                st.write(response)

    st.divider()

if __name__ == '__main__':
    csv_analyzer_app()