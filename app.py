import streamlit as st
import google.generativeai as genai
import json
import random
import math
import time

# --- Configuration and Setup ---
st.set_page_config(page_title="AI Excel Interviewer", layout="wide")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("Google API key not found. Please add `GOOGLE_API_KEY` to your Streamlit secrets.", icon="🚨")
    st.stop()

# --- Knowledge Base Loading ---
@st.cache_data
def load_questions(filepath="interview_questions.json"):
    with open(filepath, 'r') as f:
        return json.load(f)

# --- Prompt Templates ---
EVALUATION_PROMPT_TEMPLATE = """
You are an expert Excel Interview Evaluator. Your task is to analyze a candidate's answer to an interview question.
You must provide a numeric score from 1 to 5 and a brief justification for your score based on the provided rubric.
Your entire output must be a single, valid JSON object.

**Rubric:**
- 5: Excellent. The answer is accurate, complete, and demonstrates deep understanding.
- 4: Good. The answer is mostly correct but may have minor inaccuracies.
- 3: Satisfactory. The answer demonstrates a basic understanding but is incomplete or contains notable errors.
- 2: Poor. The answer is largely incorrect and shows a fundamental misunderstanding.
- 1: Very Poor. The answer is completely wrong or irrelevant.

**Interview Question:**
{question}

**Candidate's Answer:**
{answer}

**Evaluation Rubric for this question:**
{rubric}
"""

FINAL_REPORT_PROMPT_TEMPLATE = """
You are a helpful and constructive hiring manager, specializing in data roles.
Your task is to generate a final performance summary for a candidate who has just completed an Excel skills interview in Markdown format.

Based on the full transcript, provide a report with these sections:
1.  **Overall Summary:** A brief, 2-3 sentence paragraph summarizing the candidate's performance.
2.  **Strengths:** 2-3 bullet points highlighting what the candidate did well.
3.  **Areas for Improvement:** 2-3 bullet points with constructive feedback.
4.  **Final Recommendation:** A concluding sentence (e.g., "Recommend for next round," "Shows promise but needs more practice," "Not a strong fit at this time").

**Interview Transcript and Evaluations:**
{transcript}
"""

# Model configuration for JSON output
generation_config_json = genai.types.GenerationConfig(
    response_mime_type="application/json"
)

# Initialize models
eval_model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction="You are an expert Excel evaluator that only responds in valid JSON.",
    generation_config=generation_config_json
)
report_model = genai.GenerativeModel(
    "gemini-2.5-flash",
    system_instruction="You are a helpful hiring manager writing a performance report in Markdown."
)

def evaluate_answer(question, answer, rubric):
    """Uses Gemini to evaluate a single answer and return JSON."""
    prompt = EVALUATION_PROMPT_TEMPLATE.format(question=question, answer=answer, rubric=rubric)
    try:
        response = eval_model.generate_content(prompt)
        # Add a small delay to respect API rate limits
        time.sleep(1)
        return json.loads(response.text)
    except Exception as e:
        st.error(f"An error occurred during evaluation: {e}. The response may not be valid JSON.")
        return {"score": 0, "justification": f"Error during evaluation. Details: {str(e)}"}

def generate_final_report(results):
    """Uses Gemini to generate the final summary report."""
    transcript = ""
    for i, res in enumerate(results):
        transcript += f"**Question {i+1}:** {res['question']}\n"
        transcript += f"**Candidate's Answer:** {res['answer']}\n"
        transcript += f"**Score:** {res['evaluation']['score']}/5\n"
        transcript += f"**Justification:** {res['evaluation']['justification']}\n\n---\n\n"

    prompt = FINAL_REPORT_PROMPT_TEMPLATE.format(transcript=transcript)
    try:
        response = report_model.generate_content(prompt)
        time.sleep(1)
        return response.text
    except Exception as e:
        st.error(f"An error occurred while generating the report: {e}")
        return "Could not generate the final report due to an error."

# --- Streamlit App UI & Logic ---
st.title("🤖 AI Excel Interviewer (Powered by Gemini)")
st.progress(0, text="Interview Progress")
# --- State Management with Interactive Logic ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'welcome'
    st.session_state.q_index = 0
    st.session_state.results = []
    st.session_state.retry_attempt = False

    INTERVIEW_LENGTH = 3
    full_question_list = load_questions()

    if len(full_question_list) > INTERVIEW_LENGTH:
        st.session_state.interview_questions = random.sample(full_question_list, k=INTERVIEW_LENGTH)
    else:
        st.session_state.interview_questions = full_question_list

    st.session_state.messages = [{
        "role": "assistant",
        "content": f"""Hello! I'm your adaptive AI interviewer.

**Here’s how this will work:**
1.  I will ask you a series of questions to assess your Excel skills.
2.  If an answer isn't quite right, I may give you a hint and a chance to try again.
3.  The interview will adapt based on your performance and may end early if a clear skill level is determined.

This session will have up to **{len(st.session_state.interview_questions)} questions**. Ready? Type **'start'**.
"""
    }]

# --- Update Progress Bar & Average Score Display ---
total_questions = len(st.session_state.interview_questions)
questions_answered = st.session_state.q_index
progress_percent = questions_answered / total_questions if total_questions > 0 else 0

average_score = 0
if st.session_state.results:
    total_score = sum(res['evaluation']['score'] for res in st.session_state.results)
    average_score = total_score / len(st.session_state.results)

col1, col2 = st.columns(2)
with col1:
    st.progress(progress_percent, text=f"Question {questions_answered}/{total_questions}")
with col2:
    if average_score > 0:
        st.metric(label="Average Score", value=f"{average_score:.2f} / 5.0")

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main App Logic ---
if st.session_state.stage == 'interview_finished':
    st.success("The interview is complete! Generating your performance report...")
    if 'report' not in st.session_state:
        st.session_state.report = generate_final_report(st.session_state.results)
    st.markdown("---")
    st.subheader("Your Performance Report")
    st.markdown(st.session_state.report)
    st.stop()

if prompt := st.chat_input("Your answer"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.stage == 'welcome':
        if 'start' in prompt.lower():
            st.session_state.stage = 'interviewing'
            first_question = st.session_state.interview_questions[0]['question']
            st.session_state.messages.append({"role": "assistant", "content": first_question})
            with st.chat_message("assistant"):
                st.markdown(first_question)

    elif st.session_state.stage == 'interviewing':
        current_q_data = st.session_state.interview_questions[st.session_state.q_index]

        with st.spinner("Analyzing your response..."):
            evaluation = evaluate_answer(current_q_data['question'], prompt, current_q_data.get('rubric', ''))

        if evaluation['score'] < 3 and not st.session_state.retry_attempt:
            st.session_state.retry_attempt = True
            hint = current_q_data.get('hint', "Let's think about that from another angle.")
            response = f"That's not quite what I was looking for. Here's a hint: *{hint}* \n\nWhy don't you try answering that question again?"
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
        else:
            st.session_state.retry_attempt = False
            st.session_state.results.append({
                "question": current_q_data['question'], "answer": prompt, "evaluation": evaluation
            })
            st.session_state.q_index += 1

            seventy_five_percent_mark = math.ceil(total_questions * 0.75)
            if st.session_state.q_index >= seventy_five_percent_mark and average_score > 0 and average_score < 3.0:
                st.session_state.stage = 'interview_finished'
                response = "Thank you for your time. Based on the responses so far, I have enough information to complete the assessment. I will now generate your performance report."
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.rerun()

            elif st.session_state.q_index < total_questions:
                next_question = st.session_state.interview_questions[st.session_state.q_index]['question']
                response = f"Thank you. Here is the next question:\n\n{next_question}"
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
            else:
                st.session_state.stage = 'interview_finished'
                response = "Thank you, that was the final question. Please wait a moment while I generate your performance report."
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.rerun()
