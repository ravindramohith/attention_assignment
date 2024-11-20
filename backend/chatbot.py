import ollama
from typing import Dict, List
from datetime import datetime


class TravelContext:
    def __init__(self):
        self.info = {"location": None, "dates": None, "budget": None, "interests": None}
        self.messages = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if role == "user":
            # Extract entities if needed
            pass

    def get_missing_info(self) -> List[str]:
        return [k for k, v in self.info.items() if v is None]

    def clear_messages(self):
        self.messages = []


def create_travel_prompt(context: TravelContext) -> str:
    missing = context.get_missing_info()

    if missing:
        return f"""You are a travel assistant. Based on the conversation, we need: {', '.join(missing)}.
Ask naturally for ONE missing detail. Current info: {context.info}"""
    else:
        return f"""Generate a detailed travel itinerary based on:
Location: {context.info['location']}
Dates: {context.info['dates']}
Budget: {context.info['budget']}
Interests: {context.info['interests']}
Include specific places, times, and costs."""


session_contexts: Dict[str, TravelContext] = {}


def generate_response(
    session_id: str, user_input: str, message_history: List[Dict[str, str]] = None
) -> str:
    try:
        if session_id not in session_contexts:
            session_contexts[session_id] = TravelContext()

        print("MESSAGE HS, \n", message_history)
        context = session_contexts[session_id]
        context.clear_messages()

        # Use sorted message history
        if message_history:
            # Sort messages by timestamp if present
            sorted_history = (
                sorted(message_history, key=lambda x: x.get("timestamp", ""))
                if all("timestamp" in msg for msg in message_history)
                else message_history
            )

            for msg in sorted_history:
                context.add_message(msg["role"], msg["content"])

        context.add_message("user", user_input)
        prompt = create_travel_prompt(context)

        response = ollama.chat(
            model="llama2",
            messages=[
                {"role": "system", "content": prompt},
                *[
                    {"role": m["role"], "content": m["content"]}
                    for m in context.messages
                ],
            ],
            stream=False,
        )

        assistant_response = response["message"]["content"].strip()
        context.add_message("assistant", assistant_response)
        return assistant_response

    except Exception as e:
        print(f"Error: {e}")
        return "I apologize, but I'm having trouble. Could you try rephrasing that?"
