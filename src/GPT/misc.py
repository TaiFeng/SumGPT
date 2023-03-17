import openai
from langchain.llms import OpenAI
import os
import streamlit as st
from typing import Any, Dict, List, Tuple, Union


def validate_api_key(api_key: str) -> bool:
    """Validates the OpenAI API key by trying to create a completion."""
    openai.api_key = api_key
    try:
        openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=1,
            messages=[
                {"role": "user", "content": "Hello!"}
            ]
        )
        return True
    except openai.error.AuthenticationError:
        return False


def predict_token(param, chunks) -> int:
    """predict how many tokens to generate."""
    if st.session_state["OPENAI_API_KEY"] is not None:
        os.environ['OPENAI_API_KEY'] = st.session_state["OPENAI_API_KEY"]
        llm = OpenAI()
        total_token = 0
        for chunk in chunks:
            chunk_token = llm.get_num_tokens(chunk['content'])
            chunk_token += param.max_tokens_rec
            total_token += chunk_token
        if st.session_state['FINAL_SUMMARY_MODE']:
            total_token += param.max_tokens_final

        return total_token
    else:
        return 0


def predict_token_single(max_tokens, chunk) -> int:
    """predict how many tokens to generate."""
    if st.session_state["OPENAI_API_KEY"] is not None:
        os.environ['OPENAI_API_KEY'] = st.session_state["OPENAI_API_KEY"]
        llm = OpenAI()
        chunk_token = llm.get_num_tokens(chunk['content'])
        chunk_token += max_tokens

        return chunk_token
    else:
        return 0


def is_tokens_exceeded(param, chunks, max_token: int = 4096) -> Dict[str, Union[bool, str]]:
    """Checks if the number of tokens used has exceeded the limit."""

    # check recursive chunks tokens
    rec_chunks_token = []
    for chunk in chunks:
        chunk_token = predict_token_single(param.max_tokens_rec, chunk)
        rec_chunks_token.append(chunk_token)


    # check final chunks tokens
    final_prompt_token = len(chunks) * param.max_tokens_rec
    final_completion_token = param.max_tokens_final
    final_chunks_token = final_prompt_token + final_completion_token

    # evaluate
    if max(rec_chunks_token) > max_token:
        return {'exceeded': True,
                'reason': 'recursive',
                'message': f"Recursive tokens exceeded. Max tokens allowed: {max_token}. Tokens used: {max(rec_chunks_token)}\n"
                           f"(Prompt: {max(rec_chunks_token) - param.max_tokens_rec}, "
                           f"Completion: {param.max_tokens_rec})"}

    elif final_chunks_token > max_token and st.session_state['FINAL_SUMMARY_MODE']:
        return {'exceeded': True,
                'reason': 'final',
                'message': f"Final tokens exceeded. Max tokens allowed: {max_token}. Tokens used: {final_chunks_token}\n"
                           f"(Prompt: {final_prompt_token}, Completion: {final_completion_token})"}
    else:
        return {'exceeded': False,
                'reason': '',
                'message': ''}
