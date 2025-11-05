import uuid
from typing import Literal

from langgraph.constants import END
from langgraph.types import Command, interrupt

from email_responder.llm import llm
from email_responder.models import EmailAgentState, EmailClassification

def read_email(state: EmailAgentState) -> EmailAgentState:
    """Read an email from an external source and adds it to the state"""
    pass

def classify_intent(state: EmailAgentState) -> EmailAgentState:
    """Use LLM to classify email intent and urgency"""

    structured_llm = llm.with_structured_output(
        EmailClassification
    )
    classification_prompt = f"""
    Analyze the customer email and classify it:

    Email: {state['email_content']}
    From: {state['sender_email']}

    Provide classification, including intent, urgency, topic and summary.
    """

    classification = structured_llm.invoke(classification_prompt)
    return {"classification": classification}


class SearchApiError(BaseException):
    """Exception raised when an error occurs during search"""


def search_documentation(state: EmailAgentState) -> EmailAgentState:
    """Search documentation for relevant information. """

    # Build search query from classification.
    classification = state.get("classification", "")
    query = f"{classification.get('intent', '')} {classification.get('topic', '')}"

    try:
        # TODO: Implement search logic here
        print(f'Returning dummy search using {query}')
        search_results = [
            "search result 1",
            "search result 2",
            "search result 3",
        ]
    except SearchApiError as e:
        search_results = [f"Search result temporary unavailable: {e}"]

    return {"search_results": search_results}


def bug_tracking(state: EmailAgentState) -> EmailAgentState:
    """Update bug tracking information """
    ticket_id = f'BUG_{uuid.uuid4()}'
    return {"ticket_id": ticket_id}


def write_response(state: EmailAgentState) -> Command[Literal["human_review", "send_reply"]]:
    """Generate a response based on context and route based on quality"""

    classification = state.get("classification", "")

    context_sections = []

    if results := state.get('search_results'):
        formatted_docs = "\n".join([f"- {r}" for r in results])
        context_sections.append(f"Relevant documentation:\n{formatted_docs}")

    if history := state.get('customer_history'):
        context_sections.append(f"Customer tier: {history.get('tier', 'standard')}")

    draft_prompt = f"""
    Draft a response to this customer email:
    {state['email_content']}

    Email intent: {classification.get('intent', 'unknown')}
    Urgency level: {classification.get('urgency', 'medium')}

    {"\n".join(context_sections)}
    
    Guidelines:
    - Be professional and helpful.
    - Address their specific concern.
    - Use the provided documentation when relevant.
    - Be brief.

    """

    response = llm.invoke(draft_prompt)

    # Determine if human review is needed based on urgency and intent:
    needs_review = (
            classification.get('urgency') in ['high', 'critical'] or
            classification.get('intent') == 'complex'
    )

    if needs_review:
        goto = 'human_review'
        print('Email response needs review')
    else:
        goto = 'send_reply'

    return Command(
        update={"draft_response": response.content},
        goto=goto,
    )


def human_review(state: EmailAgentState) -> Command[Literal["send_reply", END]]:
    """Generate a response based on context and route based on quality"""

    classification = state.get("classification", "")

    # Any code before interrupt will re-run on resume
    human_decision = interrupt({
        "email_id": state['email_id'],
        "original_email": state['email_content'],
        "draft_response": state.get('draft_response', ''),
        "urgency": classification.get('urgency'),
        "intent": classification.get('intent'),
        "action": "Please review and approve/edit this response."
    })

    if human_decision.get('approved'):
        return Command(
            update={
                "draft_response": human_decision.get(
                    'edited_response', state['draft_response'])
            },
            goto='send_reply',
        )
    else:
        return Command(update={}, goto=END)


def send_reply(state: EmailAgentState) -> None:
    """Send a reply to the customer email"""
    pass

