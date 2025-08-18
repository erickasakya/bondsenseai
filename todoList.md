## Todo List to accomplish this project.
1. Build a database structure to hold the information for the different documents
2. Implement document ingestion functionality to populate the database with auction calendar and auction results documents
3. Create a state machine using Langgraph to handle user queries and manage the flow of information
4. Develop a retrieval system to fetch relevant data based on user input
5. Integrate a chat model (GroQ) to generate responses based on the retrieved data
6. Design and implement a Streamlit web interface for user interaction
7. Set up Docker for application packaging to ensure consistent deployment across environments
8. Use Docker Compose to manage multi-container applications for the backend, database, and frontend
9. Write unit tests for each component to ensure reliability and correctness


## Known nodes so far.
- `classify task/qn`: When a user types a question we know which category of question is this (Knowledge, Calender & data/yield)
- `extract_query_pram`: Given the question which parameter can be got from the question to answer the particular kind of question
- `classify_market`: Bonds are sold on primary or secondary market now depending on the question we need to determine the market and retreive accordily.
- `get_auction_date`: Retrieves the auction calendar date from the database.
- `get_bond_yield`: Fetches auction results for a specific bond type, maturity_data.
