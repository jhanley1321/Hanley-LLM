# Open-LLM (WIP)
A flexible multi-propose agentic LLM chatbot suitable for working with data at scale.
There will be specialized NLP functionality built in, given its incredible performance these tasks. Our first focus will be to get this to work as a general chat bot. 


# How to use
simply run the file on the command line for now using main.py
```
python main.py
```

# How to set up a local LLM (will be moved to it's own repo later)

First, download Ollama. Next, You will need to look up what model you want to run locally, but for the current setup, I will be using llama2 and mxbai large; you can install them with the following commands if you haven't already:

```
ollama pull llama2
ollama pull mxbai-embed-large
```


If you're using a local LLM with Ollama you will need to run 
```
ollama run  <model_name>
```

If your Ollama server for some reason shuts down or needs to be restarted simply run
```
ollama serve
```




# Current Features
* Currently set up to work with OpenAI API 
* Interact Directly with the LLM chat bot
* Interact with any tools you create or connect
* In session memory for context retention
* Context Limits

# Features Roadmap
* Enhanced multi-modal support
* Enhanced LangChain integration
* Enhanced LangGraph integration
* Palantir integration (Maybe, may not be needed )
* MCP integration
* RAG
* CAG
* RAGAS for RAg evaluation
* Basic Front-end Support with Streamlit
* Automatic tool detection
* Specialized NLP functionality
* LLM + NLP Hybrid system for NLP tasks
* BI and Analytics assistant
* Data science/ML assistant
* Docker Container
* Vector Database Support for quick semantic search (Chroma for now)
* PSQL support for Chat history (With slow, full semantic search)
* Redis Layer support for caching 





# Conventional Commit Types

## 🔧 Core Conventional Commit Types

| Type         | Description                                                                       |
|--------------|-----------------------------------------------------------------------------------|
| **feat**     | A new feature                                                                     |
| **fix**      | A bug fix                                                                         |
| **docs**     | Documentation only changes                                                        |
| **style**    | Changes that do not affect the meaning of the code (white-space, formatting, etc) |
| **refactor** | A code change that neither fixes a bug nor adds a feature                         |
| **perf**     | A code change that improves performance                                           |
| **test**     | Adding or correcting tests                                                        |
| **build**    | Changes that affect the build system or external dependencies (e.g., npm)         |
| **ci**       | Changes to CI configuration files and scripts (e.g., GitHub Actions, Travis)      |
| **chore**    | Other changes that don't modify src or test files (e.g., release notes, configs)  |
| **revert**   | Reverts a previous commit                                                         |

## 🧪 Extended/Optional Types

| Type         | Description                                                         |
|--------------|---------------------------------------------------------------------|
| **wip**      | Work in progress; not ready for production                          |
| **merge**    | A merge commit                                                      |
| **hotfix**   | A quick fix for a critical issue                                    |
| **security** | Security-related changes                                            |
| **deps**     | Updating or pinning dependencies                                    |
| **infra**    | Infrastructure-related changes (e.g., Terraform, Dockerfiles)       |
| **ux**       | Changes affecting user experience (not necessarily features)        |
| **i18n**     | Internationalization and localization changes                       |
| **release**  | Version bumps, changelog updates, tagging, etc.                     |
| **env**      | Environment-related changes (e.g., `.env` files, deployment configs)|

## 📚 Optional Scopes

You can add an optional scope in parentheses to clarify what part of the app is affected.

# Contact Me

If you'd like to get in touch, feel free to reach out via email or connect with me on LinkedIn:

- **Email:** [carljames1321@gmail.com](mailto:carljames1321@gmail.com)
- **LinkedIn:** [https://www.linkedin.com/in/jchanley/](https://www.linkedin.com/in/jchanley/)