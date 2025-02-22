# Azure AI Foundry: Swiss FSI Agent Labs
> [!NOTE]  
> The APIs utilized in these labs are intended solely for demonstration purposes and should not be used for any purpose other than experimentation.

Welcome to the **Azure AI Foundry Swiss FSI agent labs**! This repository demonstrates how to build an end-to-end KYC (Know Your Customer) solution for the banking industry using various Azure AI capabilities. 

## 🎯 Overview

This solution demonstrates a complete FSI compliance workflow:
- Extract and structure KYC data from diverse sources
- Create intelligent agents to maintain and update the KYC data through natural conversations and real-time Bing searches
- Deploy specialized multi-agent systems for advanced compliance decisions and risk assessment
- Evaluate agent performance and accuracy
- Monitor and debug production deployments

## 📚 Labs & Services

| Lab | Description | Azure Services Used |
|-----|-------------|-------------------|
| **Lab 01 – Data Extraction** | Extract structured KYC data from unstructured sources:<br>• Process text documents<br>• Transcribe and analyze audio interviews<br>• Convert extracted data into normalized JSONs<br>• Store results for further processing | • Azure AI Content Understanding |
| **Lab 02 – Single-Agent Chat** | Create an intelligent KYC interview agent:<br>• Connect to Cosmos DB for customer data<br>• Integrate with Bing Search for real-time data<br>• Handle conversations using Azure AI Agent Service | • Azure AI Agent Service<br>• Azure Cosmos DB<br>• Bing Search<br>• Azure Identity |
| **Lab 03 – Multi-Agent System** | Build a watch list screening system with specialized agents:<br>• KYC Officer: Customer data validation<br>• Account Manager: Account operations<br>• Risk Officer: Final compliance decisions<br>• Integrate with Swiss registries (Zefix, FINMA, SHAB) | • Azure OpenAI Service<br>• Semantic Kernel<br>• Azure Identity<br>• Custom APIs |
| **Lab 04 – Evaluation** | Set up comprehensive testing framework:<br>• Define evaluation metrics<br>• Create test scenarios<br>• Run automated evaluations<br>• Generate performance reports | • Azure AI Evaluate SDK<br>• Azure Monitor<br>• Azure Application Insights |
| **Lab 05 – Monitoring / Tracing** | Implement production-grade observability:<br>• Set up distributed tracing<br>• Enable detailed logging | • Application Insights<br>• Azure Monitor<br>• OpenTelemetry |

## Repository Structure

```
azure-ai-foundry-swiss-fsi-labs/
├── README.md
├── data/
│   └── kyc_results_outdated.jsonl           # Sample KYC records
└── labs/
    ├── 01-extract-unstructured/             # Content extraction lab
    │   ├── main.ipynb                       # Main extraction workflow
    │   ├── content_understanding.py         # Azure AI Content Understanding client
    │   ├── utils.py                         # Helper functions
    │   └── requirements.txt                 # Lab dependencies
    │
    ├── 02-chat-single-agent/                # Single agent lab
    │   ├── main.ipynb                       # Main chat agent workflow
    │   ├── chat_ui.py                       # Gradio chat interface
    │   ├── kyc_functions.py                 # Cosmos DB operations
    │   ├── initialize_cosmos_db.py          # Database setup script
    │   └── requirements.txt                 # Lab dependencies
    │
    ├── 03-conflict-detection-multi-agent/   # Multi-agent lab
    │   ├── main.ipynb                       # Main multi-agent workflow
    │   ├── chat_ui.py                       # Gradio multi-agent interface
    │   ├── shared_state.py                  # Shared agent context
    │   ├── plugin_logger.py                 # Plugin activity logging
    │   ├── bank_api.py                      # Banking operations API
    │   ├── bank_plugin.py                   # Banking semantic plugin
    │   ├── finma_api.py                     # FINMA registry API
    │   ├── finma_plugin.py                  # FINMA semantic plugin
    │   ├── zefix_api.py                     # Zefix registry API
    │   ├── zefix_plugin.py                  # Zefix semantic plugin
    │   ├── shab_api.py                      # SHAB gazette API
    │   ├── shab_plugin.py                   # SHAB semantic plugin
    │   ├── seco_api.py                      # SECO sanctions API
    │   ├── seco_plugin.py                   # SECO semantic plugin
    │   └── requirements.txt                 # Lab dependencies
    │
    ├── 04-evaluation/                       # Evaluation lab
    │   ├── main.ipynb                       # Main evaluation workflow
    │   ├── run_evals.ipynb                  # Evaluation runner
    │   ├── kyc_functions.py                 # KYC functions to evaluate
    │   ├── evals.jsonl                      # Evaluation test cases
    │   └── requirements.txt                 # Lab dependencies
    │
    └── 05-monitoring-tracing/               # Monitoring lab
        ├── main.ipynb                       # Main monitoring workflow
        ├── kyc_functions.py                 # Instrumented KYC functions
        └── requirements.txt                 # Lab dependencies
```

## About This Project

This demo showcases a **pro-code** approach to Azure AI Foundry, demonstrating how to orchestrate multiple Azure AI services for realistic banking compliance workflows. 

**Technical Highlights:**
- Semantic Kernel for multi-agent orchestration
- Azure OpenAI for natural language understanding
- API integrations with Swiss registries
- Distributed tracing with OpenTelemetry

**Enjoy exploring these labs!** Feel free to modify, extend, or adapt them to your own compliance workflows. If you have any questions or feedback, [open an issue](#) in this repository.