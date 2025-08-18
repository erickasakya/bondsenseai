## BondSense AI

BondSense AI is an application that helps you make sense of the bonds market breaking the finance jargon arround bonds.

The application makes use of Bank of Uganda action calender documents to answer questions around when is the next or was the last bond auction of a particular bond type. 

The application is able to answer question in regards to returns or yield of a particular bond. Forexampl if I wanted to know the current return or interest rate on a 15years bond in uganda. BondSense AI makes use of the Bank of Uganda auction results documents to answer this kind of question.

Also questions in line with general understanding of the bond market like what's a bond or which types are available in the ugandan market, the system uses general knowledge to explain the terms in the human understandable language.

## APP features
Knowledge Base: Document ingestion into a local database e.g Auction Calender, monthly & week Auction results   

StateMachine: This is done using langgraph to build nodes that perform tasks to answer user questions.

Retrieve: Given a user input, relevant data is retrieved from storage.

Generate: A chatmodel LLM(GroQ) produces an answer using a prompt that includes both the question with the retrieved data.

Chat: Streamlit web interface for seamless user interaction

## Tools Used
- Python -> Backend development
- Langchain -> LLM framework
- Langgraph -> Agent build
- Postgresql -> Local db to knowledge base
- Streamlit -> Frontend/Chat Builder
- Docker -> Application packaging tool
- Docker Compose -> Application deployment

## User Flow

![User Flow](https://github.com/erickasakya/bondsenseai/blob/main/BondSenseAi.drawio.png?raw=true)