import json
import time
from typing import List, Dict, Any
import gradio as gr
from gradio import ChatMessage
import asyncio
from dataclasses import asdict
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from plugin_logger import get_last_calls

from agents import create_kernel, BankingContext, KYC_OFFICER, ACCOUNT_MANAGER, RISK_OFFICER
from shared_state import bank_api

def convert_dict_to_chatmessage(msg: dict) -> ChatMessage:
    return ChatMessage(role=msg["role"], content=msg["content"], metadata=msg.get("metadata"))

def create_chat_interface(chat: AgentGroupChat):
    last_message = None
    last_message_timestamp = 0
    context = BankingContext()
    
    def refresh_accounts():
        accounts = bank_api.list_accounts()
        accounts_text = "Current Accounts:\n\n"
        for acc in accounts:
            accounts_text += (f"Owner: {acc.owner.name}\n"
                            f"Type: {acc.owner.type.value}\n"
                            f"Status: {acc.status.value}\n"
                            f"Balance: {acc.balance}\n"
                            f"{'=' * 40}\n")
        return accounts_text

    def refresh_plugin_calls():
        calls = get_last_calls()
        calls_text = "Recent Plugin Calls:\n\n"
        for call in calls:
            calls_text += (f"Plugin: {call.plugin_type.value}\n"
                         f"Function: {call.function_name}\n"
                         f"Input: {json.dumps(call.input_data, indent=2)}\n"
                         f"Output: {call.output}\n"
                         f"Time: {call.timestamp}\n"
                         f"{'=' * 40}\n")
        return calls_text

    async def banking_chat(user_message: str, history_kyc: List[dict], history_risk: List[dict], history_account: List[dict]):
        nonlocal last_message, last_message_timestamp
        
        if last_message == user_message and time.time() - last_message_timestamp < 5:
            yield history_kyc, history_risk, history_account, refresh_plugin_calls(), refresh_accounts()
            return
            
        last_message = user_message
        last_message_timestamp = time.time()

        # Add user message to all chatboxes
        user_msg = ChatMessage(role="user", content=user_message)
        history_kyc = list(history_kyc)  # Create new list to avoid modifying input
        history_risk = list(history_risk)
        history_account = list(history_account)
        
        history_kyc.append(asdict(user_msg))
        history_risk.append(asdict(user_msg))
        history_account.append(asdict(user_msg))
        
        yield history_kyc, history_risk, history_account, refresh_plugin_calls(), refresh_accounts()

        # Parse commands and update context
        if user_message.startswith("new customer"):
            parts = user_message.split()
            context.current_customer_name = " ".join(parts[2:-2] if "company" in parts else parts[2:])
            context.is_company = "company" in parts
            if context.is_company:
                context.uid = parts[-1]
        elif user_message.startswith("review account"):
            context.current_account_id = user_message.split()[-1]

        message = ChatMessageContent(
            role=AuthorRole.USER,
            content=f"{user_message}\nContext: {context}"
        )
        
        await chat.add_chat_message(message)
        
        try:
            async for response in chat.invoke():
                if response and response.name:
                    agent_msg = ChatMessage(
                        role="assistant",
                        content=response.content
                    )
                    
                    # Route message to appropriate chatbox
                    if response.name == KYC_OFFICER:
                        history_kyc.append(asdict(agent_msg))
                    elif response.name == RISK_OFFICER:
                        history_risk.append(asdict(agent_msg))
                    elif response.name == ACCOUNT_MANAGER:
                        history_account.append(asdict(agent_msg))
                        
                    yield history_kyc, history_risk, history_account, refresh_plugin_calls(), refresh_accounts()
                    
        except Exception as e:
            error_msg = ChatMessage(
                role="assistant",
                content=f"Error: {str(e)}",
                metadata={"error": True}
            )
            error_dict = asdict(error_msg)
            history_kyc.append(error_dict)
            history_risk.append(error_dict)
            history_account.append(error_dict)
            yield history_kyc, history_risk, history_account, refresh_plugin_calls(), refresh_accounts()

    with gr.Blocks(title="Banking Multi-Agent System", css="""
        .message.agent-message { border-radius: 5px; margin: 5px 0; padding: 10px; }
        .message.agent-message p { margin: 5px 0; }
        .message.agent-message h3 { margin: 0 0 10px 0; }
    """) as ui:
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Row():
                    with gr.Column():
                        chatbox_kyc = gr.Chatbot(
                            label="🔍 KYC Officer",
                            height=400,
                            type="messages",
                            render_markdown=True,
                        )
                    with gr.Column():
                        chatbox_risk = gr.Chatbot(
                            label="⚠️ Risk Officer",
                            height=400,
                            type="messages",
                            render_markdown=True,
                        )
                    with gr.Column():
                        chatbox_account = gr.Chatbot(
                            label="💼 Account Manager",
                            height=400,
                            type="messages",
                            render_markdown=True,
                        )
                msg = gr.Textbox(
                    label="Event Type",
                    placeholder="Examples:\n- new customer John Doe\n- new customer ACME Corp company CHE-123.456.789\n- Perform account review for <account>",
                    lines=3
                )
                                
                # Add sample query buttons
                with gr.Row():
                    sanctioned_name = bank_api.list_accounts()[1].owner.name  # Get the sanctioned person's name
                    gr.Button(f"Review {sanctioned_name}'s Account").click(
                        fn=lambda name=sanctioned_name: f"Perform an Account Review for {name}",
                        outputs=msg
                    )
                    gr.Button("Create Microsoft CH Account").click(
                        fn=lambda: "new customer Microsoft Schweiz GmbH company CHE-110.088.994",
                        outputs=msg
                    )
                    gr.Button("Create Swissair Account").click(
                        fn=lambda: "new customer swissAir APS SA",
                        outputs=msg
                    )
                    gr.Button("Create Unexisting Account").click(
                        fn=lambda: "new customer MySuperAgent24 GmbH company",
                        outputs=msg
                    )
                with gr.Row():
                    submit = gr.Button("Submit", variant="primary")
                    clear = gr.Button("Clear Chat")
            
            with gr.Column(scale=1):
                plugin_monitor = gr.TextArea(
                    label="Plugin Activity",
                    value=refresh_plugin_calls(),
                    interactive=False
                )
                accounts_monitor = gr.TextArea(
                    label="Accounts",
                    value=refresh_accounts(),
                    interactive=False
                )
                refresh_btn = gr.Button("Refresh")

        # Event handlers
        msg.submit(
            fn=banking_chat,
            inputs=[msg, chatbox_kyc, chatbox_risk, chatbox_account],
            outputs=[chatbox_kyc, chatbox_risk, chatbox_account, plugin_monitor, accounts_monitor]
        )
        submit.click(
            fn=banking_chat,
            inputs=[msg, chatbox_kyc, chatbox_risk, chatbox_account],
            outputs=[chatbox_kyc, chatbox_risk, chatbox_account, plugin_monitor, accounts_monitor]
        )
        clear.click(
            lambda: ([], [], [], "", ""), 
            outputs=[chatbox_kyc, chatbox_risk, chatbox_account, msg, plugin_monitor]
        )
        refresh_btn.click(
            fn=lambda: (refresh_plugin_calls(), refresh_accounts()),
            outputs=[plugin_monitor, accounts_monitor]
        )

    return ui

