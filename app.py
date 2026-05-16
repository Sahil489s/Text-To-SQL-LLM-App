import os
import sqlite3
import streamlit as st

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# -------------------------------
# DATABASE SETUP
# -------------------------------

DATABASE = "student.db"


def create_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS STUDENT(
        NAME TEXT,
        COURSE TEXT,
        SECTION TEXT,
        MARKS INT
    )
    """)

    # Insert sample data only if table is empty
    cursor.execute("SELECT COUNT(*) FROM STUDENT")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_data = [
            ("Sahil", "Data Science", "A", 90),
            ("Rahul", "Machine Learning", "B", 85),
            ("Priya", "Data Science", "A", 95),
            ("Aman", "AI", "C", 88),
            ("Neha", "Cyber Security", "B", 80)
        ]

        cursor.executemany(
            "INSERT INTO STUDENT VALUES (?, ?, ?, ?)",
            sample_data
        )

    conn.commit()
    conn.close()


# -------------------------------
# GENERATE SQL QUERY USING GROQ
# -------------------------------

def get_sql_query(user_query):
    try:
        prompt = ChatPromptTemplate.from_template("""
        You are an expert in converting English questions into SQL queries.

        The SQL database has the name STUDENT and contains the following columns:
        NAME, COURSE, SECTION, MARKS

        Example 1:
        Question: How many records are present?
        SQL Query:
        SELECT COUNT(*) FROM STUDENT;

        Example 2:
        Question: Show all students studying Data Science
        SQL Query:
        SELECT * FROM STUDENT WHERE COURSE = "Data Science";

        Rules:
        - Only return SQL query
        - Do not return explanation
        - Do not use ``` or sql word
        - Query must be valid SQLite SQL

        User Question:
        {user_query}
        """)

        llm = ChatGroq(
            groq_api_key=os.environ.get("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile"
        )

        chain = prompt | llm | StrOutputParser()

        response = chain.invoke({
            "user_query": user_query
        })

        return response.strip()

    except Exception as e:
        return f"ERROR: {str(e)}"


# -------------------------------
# EXECUTE SQL QUERY
# -------------------------------

def execute_sql_query(sql_query):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(sql_query)

        rows = cursor.fetchall()

        conn.commit()
        conn.close()

        return rows

    except Exception as e:
        return [("Database Error", str(e))]


# -------------------------------
# STREAMLIT APP
# -------------------------------

def main():

    st.set_page_config(
        page_title="Text To SQL App",
        page_icon="🤖",
        layout="centered"
    )

    st.title("🤖 Text To SQL AI App")

    st.write("Ask questions about the STUDENT database.")

    user_query = st.text_input(
        "Enter your question:",
        placeholder="Example: Show all students in Data Science"
    )

    submit = st.button("Generate Result")

    if submit:

        if not user_query.strip():
            st.warning("Please enter a question.")
            return

        with st.spinner("Generating SQL Query..."):

            sql_query = get_sql_query(user_query)

        st.subheader("Generated SQL Query")

        st.code(sql_query, language="sql")

        # Handle LLM Errors
        if sql_query.startswith("ERROR"):
            st.error(sql_query)
            return

        # Execute Query
        results = execute_sql_query(sql_query)

        st.subheader("Query Results")

        if len(results) == 0:
            st.info("No records found.")

        else:
            for row in results:
                st.write(row)


# -------------------------------
# RUN APP
# -------------------------------

if __name__ == "__main__":

    create_database()

    main()