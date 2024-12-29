"""
1.0.0
summarize, translate가 없는 버전
"""
import snowflake.connector
from snowflake.snowpark import Session
from snowflake.cortex import Complete, ExtractAnswer, Sentiment, Summarize, Translate

from typing import Any, Dict, List, Optional
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

# Connecting to Snowflake & snowpark
if 'CONN' not in st.session_state or st.session_state.CONN is None:
    st.session_state.CONN = snowflake.connector.connect(
        user=os.getenv('USER'),
        password=os.getenv('PASSWORD'),
        account=os.getenv('ACCOUNT'),
        warehouse=os.getenv('WAREHOUSE'),
        database=os.getenv('DATABASE'),
        schema=os.getenv('SCHEMA'),
        role=os.getenv('ROLE')
)

if 'SEMANTIC_MODEL_FILE' not in st.session_state or st.session_state.SEMANTIC_MODEL_FILE is None:
    st.session_state.SEMANTIC_MODEL_FILE = f"@{os.getenv('DATABASE')}.{os.getenv('SCHEMA')}.{os.getenv('STAGE')}/{os.getenv('FILE')}"

if 'HOST' not in st.session_state or st.session_state.HOST is None:
    st.session_state.HOST = os.getenv('HOST')

#initial example messages
examples = [
    "23년도 매출이 높은 상위 10개 브랜드를 매출금액별로 알려줘",
    "브랜드 중에서 온라인 매출의 비중이 가장 높은 브랜드는?",
    "뷰티 상품군에서 24년도 온라인 채널에서 매출 상위 제품과 매출액을 알려줘",
    "숨37 브랜드의 23년도 오프라인, 온라인 채널별 월별 추이를 보여줘",
    "온더바디 브랜드의 24년도 국내 월별 매출액은?",
    "뷰티 제품군에서 24년도 해외 판매 실적을  상품별로 알려줘",
    "더후 브랜드의 유럽 판매실적을 월별로 알려줘",
    "뷰티 상품군에서 24년도 기준 매출액이 큰 순서로 알려줘",
    "23년도에 해외 오프라인에서 매출액이 큰 상위 5개 브랜드는?",
    "23년도 6,7,8월 매출액 대비 24년도 6,7,8월 매출액 차이가 가장 큰 상위 5개 브랜드는?"
]
initial_messages = f"이런 질문은 어때요?  \n  1. {examples[0]}  \n  1. {examples[1]}    \n  1. {examples[2]}    \n  1. {examples[3]}    \n  1. {examples[4]}    \n  1. {examples[5]}    \n  1. {examples[6]}    \n  1. {examples[7]}    \n  1. {examples[8]}    \n  1. {examples[9]}  "

#functions
def send_message(prompt: str) -> Dict[str, Any]:
    """Calls the REST API and returns the response."""
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "semantic_model_file": st.session_state.SEMANTIC_MODEL_FILE,
    }
    resp = requests.post(
        url=f"https://{st.session_state.HOST}/api/v2/cortex/analyst/message",
        json=request_body,
        headers={
            "Authorization": f'Snowflake Token="{st.session_state.CONN.rest.token}"',
            "Content-Type": "application/json",
        },
    )
    request_id = resp.headers.get("X-Snowflake-Request-Id")
    if resp.status_code < 400:
        return {**resp.json(), "request_id": request_id}  # type: ignore[arg-type]
    else:
        raise Exception(
            f"Failed request (id: {request_id}) with status {resp.status_code}: {resp.text}"
        )

def process_message(prompt: str) -> None:
    """Processes a message and adds the response to the chat."""
    st.session_state.messages.append(
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    )
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("질문을 해석하는 중입니다..."):
            response = send_message(prompt=prompt)
            request_id = response["request_id"]
            content = response["message"]["content"]
            content_sql_tf = pd.DataFrame(content)['type'].isin(['sql']).any()
        #SQL 생성했으면
        if content_sql_tf:
            answer = "아래 결과를 확인하세요."
            for item in content:    
                if item["type"] == "sql":
                    with st.spinner("데이터를 불러오는 중입니다..."):
                        df = pd.read_sql(item["statement"], st.session_state.CONN)
                        content.append({'type':'df', 'data':df})
            for item in content:    
                if item['type'] == 'text':
                    item['text'] = answer
        else:
            for item in content:
                if item['type'] == 'text':
                    item['text'] = "죄송해요. 질문이 잘 이해되지 않았습니다. 다시 말해 주시거나 더 많은 맥락을 제공해 주시겠어요?"
        display_content(content=content, request_id=request_id)  # type: ignore[arg-type]
    st.session_state.messages.append(
        {"role": "assistant", "content": content, "request_id": request_id}
    )

def display_content(
    content: List[Dict[str, str]],
    request_id: Optional[str] = None,
    message_index: Optional[int] = None,
) -> None:
    """Displays a content item for a message."""
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        if item['type'] == 'sql':
            sql = item['statement']
        if item['type'] == 'df':
            with st.expander("조희 결과", expanded=True):
                data_tab, line_tab, bar_tab, sql_tab = st.tabs(
                    ["Data", "Line Chart", "Bar Chart", "SQL"]
                )
                df = item['data']
                data_tab.dataframe(df)
                if len(df.columns) > 1:
                    df = df.set_index(df.columns[0])
                with line_tab:
                    st.line_chart(df)
                with bar_tab:
                    st.bar_chart(df)
                with sql_tab:
                    st.code(sql, language='sql')

st.header("Cortex Analyst for LG생활건강")
st.markdown('`v1.0.0-poc`')

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {"role": "assistant", "content": [{
            'type': 'text',
            'text': initial_messages
        }]
        }
    )

for message_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        display_content(
            content=message["content"],
            request_id=message.get("request_id"),
            message_index = message_index
        )

if user_input := st.chat_input("What is your question?"):
    process_message(prompt=user_input)
