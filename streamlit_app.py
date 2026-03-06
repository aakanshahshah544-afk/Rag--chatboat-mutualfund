import sys
from pathlib import Path

# Make sure the project root is on the path so imports work
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from phase3_rag import RAGChain

st.set_page_config(page_title="Groww RAG Chatbot", page_icon="💬")

st.title("Groww RAG Chatbot")
st.markdown("Ask factual questions about mutual funds from Groww data.")

# Initialize RAG chain in session state
if 'rag_chain' not in st.session_state:
    with st.spinner("Loading RAG system..."):
        st.session_state.rag_chain = RAGChain()

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about mutual funds..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = st.session_state.rag_chain.query(prompt)
                response = result.get("answer", "Sorry, I couldn't find an answer.")
                citation = result.get("citation")
                if citation:
                    response += f"\n\n**Source:** {citation}"
            except Exception as e:
                response = f"Error: {str(e)}"
        st.markdown(response)
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})