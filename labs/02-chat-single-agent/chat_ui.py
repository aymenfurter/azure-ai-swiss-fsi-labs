import json
import time
from typing import List, Callable, Any
import gradio as gr
from gradio import ChatMessage

from azure.ai.projects.models import (
    AgentEventHandler,
    RunStep,
    RunStepDeltaChunk,
    ThreadMessage,
    ThreadRun,
    MessageDeltaChunk,
)


class EventHandler(AgentEventHandler):
    def __init__(self):
        super().__init__()
        self._current_message_id = None
        self._accumulated_text = ""
        self._current_tools = {}
        self.conversation = None
        self.create_tool_bubble_fn = None

    def on_message_delta(self, delta: MessageDeltaChunk) -> None:
        if delta.id != self._current_message_id:
            if self._current_message_id is not None:
                print()
            self._current_message_id = delta.id
            self._accumulated_text = ""
            print("\nassistant> ", end="")

        partial_text = ""
        if delta.delta.content:
            for chunk in delta.delta.content:
                partial_text += chunk.text.get("value", "")
        self._accumulated_text += partial_text
        print(partial_text, end="", flush=True)

    def on_thread_message(self, message: ThreadMessage) -> None:
        if message.status == "completed" and message.role == "assistant":
            print()
            self._current_message_id = None
            self._accumulated_text = ""

    def on_thread_run(self, run: ThreadRun) -> None:
        print(f"thread_run status > {run.status}")
        if run.status == "failed":
            print(f"error > {run.last_error}")

    def on_run_step(self, step: RunStep) -> None:
        print(f"step> {step.type} status={step.status}")
        
        if step.status == "completed" and step.step_details and step.step_details.tool_calls:
            for tcall in step.step_details.tool_calls:
                if getattr(tcall, "function", None):
                    fn_name = tcall.function.name
                    try:
                        output = json.loads(tcall.function.output)
                        
                        if fn_name == "get_kyc_data":
                            message = f"Found KYC record for {output.get('full_name', 'unknown person')}"
                            
                            if self.create_tool_bubble_fn:
                                self.create_tool_bubble_fn(fn_name, message, tcall.id)
                        
                        elif fn_name == "update_kyc_data":
                            record = output.get('record', {})
                            message = f"Updated KYC record for {record.get('full_name', 'unknown person')}"
                            if self.create_tool_bubble_fn:
                                self.create_tool_bubble_fn(fn_name, message, tcall.id)
                    except json.JSONDecodeError:
                        print(f"Error parsing tool output: {tcall.function.output}")

    def on_run_step_delta(self, delta: RunStepDeltaChunk) -> None:
        if delta.delta.step_details and delta.delta.step_details.tool_calls:
            for tcall in delta.delta.step_details.tool_calls:
                if getattr(tcall, "function", None):
                    print(f"partial function call> {tcall.function}")

def convert_dict_to_chatmessage(msg: dict) -> ChatMessage:
    return ChatMessage(role=msg["role"], content=msg["content"], metadata=msg.get("metadata"))

def create_chat_interface(project_client, agent, thread):
    last_message = None
    last_message_timestamp = 0
    
    def azure_kyc_chat(user_message: str, history: List[dict]):
        nonlocal last_message, last_message_timestamp
        
        print(f"User message: {user_message}")
        if last_message == user_message and time.time() - last_message_timestamp < 5:
            return history, ""
        last_message_timestamp = time.time()

        conversation = [convert_dict_to_chatmessage(m) for m in history]
        conversation.append(ChatMessage(role="user", content=user_message))
        yield conversation, ""

        project_client.agents.create_message(thread_id=thread.id, role="user", content=user_message)

        tool_titles = {
            "get_kyc_data": "🔍 Retrieving KYC Data",
            "update_kyc_data": "✏️ Updating KYC Data",
            "bing_grounding": "🌐 Searching Web Sources"
        }

        def create_tool_bubble(tool_name: str, content: str = "", call_id: str = None):
            title = tool_titles.get(tool_name, f"🛠️ {tool_name}")
            if tool_name is None:
                return
            
            msg = ChatMessage(
                role="assistant",
                content=content,
                metadata={
                    "title": title,
                    "id": f"tool-{call_id}" if call_id else "tool-noid"
                }
            )
            conversation.append(msg)
            return msg

        event_handler = EventHandler()
        event_handler.conversation = conversation
        event_handler.create_tool_bubble_fn = create_tool_bubble

        with project_client.agents.create_stream(
            thread_id=thread.id,
            assistant_id=agent.id,
            event_handler=event_handler
        ) as stream:
            for item in stream:
                event_type, event_data, *_ = item
                
                if event_type == "thread.run.step.delta":
                    step_delta = event_data.get("delta", {}).get("step_details", {})
                    if step_delta.get("type") == "tool_calls":
                        for tcall in step_delta.get("tool_calls", []):
                            call_id = tcall.get("id")
                            if tcall.get("type") == "bing_grounding":
                                search_query = tcall.get("bing_grounding", {}).get("requesturl", "").split("?q=")[-1]
                                if search_query:
                                    create_tool_bubble("bing_grounding", f"Searching for '{search_query}'...", call_id)
                        yield conversation, ""

                elif event_type == "run_step":
                    if event_data["type"] == "tool_calls" and event_data["status"] == "completed":

                        for msg in conversation:
                            if msg.metadata and msg.metadata.get("status") == "pending":
                                msg.metadata["status"] = "done"
                        yield conversation, ""

                elif event_type == "thread.message.delta":
                    content = ""
                    citations = []  # collect citations
                    for chunk in event_data["delta"]["content"]:
                        chunk_value = chunk["text"].get("value", "")
                        content += chunk_value
                        if "annotations" in chunk["text"]:
                            for annotation in chunk["text"]["annotations"]:
                                if annotation.get("type") == "url_citation":
                                    url_citation = annotation.get("url_citation", {})
                                    citation_text = f"{annotation.get('text', '')} [{url_citation.get('title', '')}]({url_citation.get('url', '')})"
                                    citations.append(citation_text)
                    citations_str = "\n" + "\n".join(citations) if citations else ""
                    
                    if not conversation or conversation[-1].role != "assistant" or conversation[-1].metadata:
                        conversation.append(ChatMessage(role="assistant", content=content + citations_str))
                    else:
                        conversation[-1].content += content + citations_str
                    yield conversation, ""

        return conversation, ""

    return azure_kyc_chat
