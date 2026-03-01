
### Task 1: Articulate the problem and the user of your application

1. Write a succinct 1-sentence description of the problem

Our app helps first-time Bay Area home buyers identify red flags in inspection reports—a crucial step for buyers with limited property access before purchase.

2. Write 1-2 paragraphs on why this is a problem for your specific user

The housing stock is dominated by homes built in the 1950s and 1960s, and many require ongoing maintenance. Demand is strong, so listings move quickly—often selling within one to two weeks. Prices are high, which makes the stakes even greater and leaves buyers little room for mistakes.

Buyers must act quickly while juggling many property decisions and a large amount of documentation. Time to inspect and understand a property before making an offer is limited. First-time buyers face an added challenge: they often don’t know which issues to look for or how to evaluate a home, making it harder to make an informed decision under pressure.



3. Create a list of questions or input-output pairs that you can use to evaluate your application
Q: Find out the red flags in propery inspection report
A: Here are red flags from the inspection report, in order of Critical, Major and Minor

Q. List schools and their rating
A. School Quality for 1455 Bittern Dr, Sunnyvale, CA <list of schoold and their ratings>


Q. How is neighborhood 
A. The neighborhood is described as charming and well-located, with close proximity to local amenities, schools, and commuter routes. It is situated near Apple Park, which is a significant landmark in the area, indicating a desirable location.

### Task 2: Articulate your proposed solution

1. Write 1-2 paragraphs on your proposed solution.  How will it look and feel to the user? Describe the tools you plan to use to build it.

Proposed Solution: 



2.  Create an infrastructure diagram of your stack showing how everything fits together.  Write one sentence on why you made each tooling choice.
    1. LLM(s)
    2. Agent orchestration framework 
    3. Tool(s)
    4. Embedding model
    5. Vector Database
    6. Monitoring tool
    7. Evaluation framework
    8. User interface
    9. Deployment tool
    10. Any other components you need
3. What are the RAG and agent components of your project, exactly?

### Task 3: Collect your own data (RAG) and choose at least one external API to use (Agent)

**You are an AI Systems Engineer.**  The AI Solutions Engineer has handed off the plan to you. *At a minimum*, you’ll need to implement a simple Agentic RAG solution that includes two aspects:

1. Your own personal data, uploaded to your application (e.g., RAG)
2. The ability to search publicly available data (e.g., a simple agentic search tool like [Tavily](https://tavily.com/))

*Hints:*  
- *Ask other real people (ideally the people you’re building for!) what they think.*
- *What are the specific questions that your user is likely to ask of your application?  **Write these down**.*
  
**✅ Deliverables**

1. Describe the default chunking strategy that you will use for your data.  Why did you make this decision?
2. Describe your data source and the external API you plan to use, as well as what role they will play in your solution. Discuss how they interact during usage. 

### Task 4: Build an end-to-end Agentic RAG application using a production-grade stack and your choice of commercial off-the-shelf model(s)

**✅ Deliverables**

1. Build an end-to-end prototype and deploy it to a *local* endpoint
2. (Optional) Use locally-hosted OSS models instead of LLMs through the OpenAI API
3. (Optional) Deploy your prototype to public endpoint using a tool like [Vercel](http://vercel.com/), [Render](https://render.com/), or [FastAPI Cloud](https://fastapicloud.com/)

### Task 5: Prepare a test data set (either by generating synthetic data or by assembling an existing dataset) to baseline an initial evaluation with RAGAS

**You are an AI Evaluation & Performance Engineer.**  The AI Systems Engineer who built the initial RAG system has asked for your help and expertise in creating a "Golden Data Set" for evaluation.

**✅ Deliverables**

1. Assess your pipeline using the RAGAS framework, including the following key metrics: faithfulness, context precision, and context recall. Include any other metrics you feel are worthwhile to assess.   Provide a table of your output results.
2. What conclusions can you draw about the performance and effectiveness of your pipeline with this information?

### Task 6: Install an advanced retriever of your choosing in our Agentic RAG application

**You are an AI Systems Engineer.**  The AI Evaluation and Performance Engineer has asked for your help in making stepwise improvements to the application. You will work together with them on this task.

**✅ Deliverables**

1. Choose an advanced retrieval technique that you believe will improve your application’s ability to retrieve the most appropriate context.  Write 1-2 sentences on why you believe it will be useful for your use case.
2. Implement the advanced retrieval technique on your application.
3. How does the performance compare to your original RAG application? Test the new retrieval pipeline using the RAGAS frameworks to quantify any improvements. Provide results in a table.

### Task 7: Next Steps

You are the **AI Solutions Engineer** working with the **AI Evaluation & Performance Engineer**. 

1. Do you plan to keep your RAG implementation via Dense Vector Retrieval for Demo Day? Why or why not?

# Your Final Submission

Please include the following in your final submission:

1. A public (or otherwise shared) link to a **GitHub repo** that contains:
- A 5-minute (OR LESS) Loom video of a live **demo of your application** that also describes the use case.
- A **written document** addressing each deliverable and answering each question
- All relevant code
