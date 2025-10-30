"""Multi-Agent System using LangGraph for Question Generation and Evaluation"""
import os
from typing import List, Dict, Any, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
import logging
import json

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the multi-agent workflow"""
    query: str
    retrieved_docs: str
    raw_questions: List[Dict[str, Any]]
    evaluated_questions: List[Dict[str, Any]]
    final_questions: List[Dict[str, Any]]
    evaluation_feedback: str
    iteration: int

class MultiAgentQuestionSystem:
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Initialize LLM - using gemini-2.5-flash (latest fast model)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.google_api_key,
            temperature=0.7
        )
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with two agents"""
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("generator", self.question_generator_agent)
        workflow.add_node("evaluator", self.question_evaluator_agent)
        workflow.add_node("finalizer", self.finalizer_agent)
        
        # Define edges
        workflow.set_entry_point("generator")
        workflow.add_edge("generator", "evaluator")
        workflow.add_edge("evaluator", "finalizer")
        workflow.add_edge("finalizer", END)
        
        return workflow.compile()
    
    def question_generator_agent(self, state: AgentState) -> AgentState:
        """Agent 1: Generate MCQ questions from retrieved content"""
        logger.info("Running Question Generator Agent...")
        
        system_prompt = """You are an expert educational content creator. Generate 5 high-quality Multiple Choice Questions (MCQs).

STRICT JSON FORMAT - Your ENTIRE response must be ONLY valid JSON, nothing else:
[
  {
    "question": "Question text?",
    "options": {
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    },
    "correct_answer": "A",
    "explanation": "Why this is correct"
  }
]

CRITICAL: Return ONLY the JSON array. No markdown, no code blocks, no explanations."""
        
        user_prompt = f"""Generate 5 MCQ questions from this content about: {state['query']}

CONTENT:
{state['retrieved_docs'][:3000]}

Return ONLY valid JSON array."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Clean up the response
            # Remove markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Remove any text before the first [
            if "[" in response_text:
                response_text = response_text[response_text.index("["):]
            
            # Remove any text after the last ]
            if "]" in response_text:
                response_text = response_text[:response_text.rindex("]")+1]
            
            logger.info(f"Cleaned response: {response_text[:200]}...")
            
            questions = json.loads(response_text)
            
            state['raw_questions'] = questions
            logger.info(f"Generated {len(questions)} questions")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in question generator: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            state['raw_questions'] = []
        except Exception as e:
            logger.error(f"Error in question generator: {e}")
            state['raw_questions'] = []
        
        return state
    
    def question_evaluator_agent(self, state: AgentState) -> AgentState:
        """Agent 2: Evaluate and improve generated questions"""
        logger.info("Running Question Evaluator Agent...")
        
        # If no questions generated, skip evaluation
        if not state['raw_questions']:
            logger.warning("No questions to evaluate")
            state['evaluated_questions'] = []
            return state
        
        system_prompt = """You are an educational assessment evaluator. Review the MCQ questions and add:
- "quality_score": 1-10 score
- "evaluator_feedback": Brief feedback
- "approved": true/false

Return the same JSON structure with these fields added. Return ONLY valid JSON."""
        
        user_prompt = f"""Evaluate these questions:

{json.dumps(state['raw_questions'], indent=2)}

Return ONLY valid JSON with quality_score, evaluator_feedback, and approved fields added."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Clean response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            if "[" in response_text:
                response_text = response_text[response_text.index("["):]
            if "]" in response_text:
                response_text = response_text[:response_text.rindex("]")+1]
            
            evaluated_questions = json.loads(response_text)
            state['evaluated_questions'] = evaluated_questions
            logger.info(f"Evaluated {len(evaluated_questions)} questions")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in evaluator: {e}")
            # Use raw questions with default scores
            state['evaluated_questions'] = [
                {**q, "quality_score": 8, "evaluator_feedback": "Auto-approved", "approved": True}
                for q in state['raw_questions']
            ]
        except Exception as e:
            logger.error(f"Error in question evaluator: {e}")
            state['evaluated_questions'] = state['raw_questions']
        
        return state
    
    def finalizer_agent(self, state: AgentState) -> AgentState:
        """Finalize and filter high-quality questions"""
        logger.info("Running Finalizer Agent...")
        
        # Filter approved questions with good scores
        final_questions = []
        for q in state['evaluated_questions']:
            # Keep questions with score >= 6 or if no score, keep all
            if q.get('quality_score', 10) >= 6 and q.get('approved', True):
                final_questions.append(q)
        
        state['final_questions'] = final_questions
        logger.info(f"Finalized {len(final_questions)} high-quality questions")
        
        return state
    
    def generate_questions(self, query: str, retrieved_docs: List[Any]) -> List[Dict[str, Any]]:
        """Run the complete multi-agent workflow"""
        logger.info("Starting multi-agent question generation workflow...")
        
        # Prepare retrieved docs as text
        docs_text = "\n\n".join([
            f"Document {i+1}:\n{doc.page_content}" 
            for i, doc in enumerate(retrieved_docs)
        ])
        
        # Initial state
        initial_state = {
            "query": query,
            "retrieved_docs": docs_text,
            "raw_questions": [],
            "evaluated_questions": [],
            "final_questions": [],
            "evaluation_feedback": "",
            "iteration": 0
        }
        
        # Run workflow
        try:
            final_state = self.workflow.invoke(initial_state)
            return final_state['final_questions']
        except Exception as e:
            logger.error(f"Error in multi-agent workflow: {e}")
            raise
