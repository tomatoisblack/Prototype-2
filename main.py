import os
from dotenv import load_dotenv
import openai
import streamlit as st
import time

# Load environment variables
load_dotenv()

# Retrieve the API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key is None:
    raise ValueError("API key is not set. Check your .env file.")

# Initialize the OpenAI client
client = openai.Client(api_key=openai_api_key)

# Set up the Streamlit front end page with wide layout
st.set_page_config(page_title="Conversational Design Assistant", page_icon=":books:", layout="wide")

# Apply custom CSS to extend the chat message width
st.markdown(
    """
    <style>
    .st-chat-message {
        max-width: 90%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state for managing the application state
if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# Main interface
st.title("Design Assistant Prototype #2")
st.write("Blindspot proof your project through conversations")

# Display thread ID if it exists
if st.session_state.thread_id:
    st.write("Thread ID:", st.session_state.thread_id)

# Button to initiate the chat session
if st.button("Start Chatting..."):
    st.session_state.start_chat = True
    # Create a new thread for this chat session only if it's not already created
    if st.session_state.thread_id is None:
        try:
            chat_thread = client.beta.threads.create()
            st.session_state.thread_id = chat_thread.id
            st.rerun()  # Refresh the page to show the thread ID
        except Exception as e:
            st.error(f"Error creating thread: {e}")

# Check if chat has started
if st.session_state.start_chat:
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show existing messages if any...
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input for the user
    if prompt := st.chat_input("What's new?"):
        # Add user message to the state and display on the screen
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # Add the user's message to the existing thread
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id, role="user", content=prompt
            )

            # Create a run with additional instructions
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id="asst_75HrDxF3zh1LE8PM4pdRvBOs",  # Updated with your new assistant ID
                instructions="Prompts from the user needs may come in many forms. It might be a research to start the project or to define the objective, pain-points, limitations, problems, research for user testing, etc. You are an expert at researching any potential given topic/question by the user. You should provide correction if the user has misinformation. You should provide relevant references or things that might be considered relevant research to the user’s question or project. You should provide realistic answers rather than a vague answer. If you need more information to assist the user, but can’t due to lack of input from the user, ask critical questions that will come into play, and utilize iterative questioning to gain context of the user's project."
            )

            # Show a spinner while the assistant is thinking...
            with st.spinner("Wait... Generating response..."):
                while run.status != "completed":
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id, run_id=run.id
                    )

                # Retrieve messages added by the assistant
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                # Process and display assistant messages
                assistant_messages_for_run = [
                    message for message in messages if message.run_id == run.id and message.role == "assistant"
                ]

                for message in assistant_messages_for_run:
                    try:
                        # Check if 'content' exists in the message and is not empty
                        if message.content:
                            # Extract the text from the content blocks
                            content_blocks = message.content
                            content_texts = [block.text.value for block in content_blocks if block.type == "text"]
                            content = "\n".join(content_texts)

                            st.session_state.messages.append({"role": "assistant", "content": content})
                            with st.chat_message("assistant"):
                                st.markdown(content, unsafe_allow_html=True)
                        else:
                            st.error("Content not found or empty in the message.")
                    except Exception as e:
                        st.error(f"Error processing message: {e}")
                        
        except Exception as e:
            st.error(f"Error communicating with assistant: {e}")
            st.error("Please check your API key and assistant ID.")
