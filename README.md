# AI CODEFIX 2025

## The Ultimate AI-Resistant Coding Competition

*Organized by*: Dept. of AI&ML & AI&DS
*In Collaboration with*: AI Planet, Agrowvitz, Tensor AI Club

---

## About The Competition

AI CODEFIX is a multi-round coding competition that tests true engineering skills in the age of AI. Our challenges are specifically designed to be *AI-resistant* - participants cannot simply paste problems into ChatGPT and expect correct solutions. Success requires genuine understanding, debugging skills, and algorithmic thinking.

### Our Philosophy

- *Skill Over Tools*: We test what participants actually know, not what they can copy
- *Debug-First Approach*: Most challenges involve fixing buggy code rather than writing from scratch
- *Real-World Relevance*: Problems mirror actual debugging scenarios engineers face daily
- *Fair but Challenging*: Partial credit ensures effort is rewarded while excellence stands out

---

## Competition Structure

### Round 1: Easy - Wumpus World Navigator

*Domain*: Pathfinding Algorithms

A classic AI problem reimagined. Debug a buggy A* pathfinding agent that must navigate a grid world with environmental hazards.

*What You'll Do:*
- Fix bugs in an A* search implementation
- Handle environmental percepts (obstacles, costs, dangers)
- Ensure the agent finds optimal paths while avoiding hazards
- Debug pathfinding logic and heuristic calculations

*Skills Tested:*
- Graph search algorithms (A*)
- Heuristic design
- State machine logic
- Systematic debugging

*Files:*
- wumpus_world.py - Buggy implementation to fix
- validator.py - Test runner
- test_cases.json - Test configurations

---

### Round 2: Medium - Database Insights Agent

*Domain*: Data Analysis & Automation

Build an intelligent agent that analyzes any SQLite database and automatically generates a comprehensive report with visualizations, then emails it.

*What You'll Do:*
- Connect to and explore an unknown database schema
- Extract meaningful statistics and patterns
- Generate professional visualizations (charts, graphs)
- Compile findings into a formatted report
- Automate email delivery with attachments

*Skills Tested:*
- SQL queries and database navigation
- Data analysis with pandas
- Data visualization (matplotlib/seaborn)
- Report generation
- Email automation (SMTP)
- Code organization and error handling

*Key Requirements:*
- Handle ANY database structure automatically
- Generate at least 3 meaningful visualizations
- Professional report formatting (HTML or PDF)
- Successfully send email with attachments

---

### Round 3: Hard Challenges

Three challenging problems designed to test deep understanding. Teams may receive different hard challenges.

---

#### Hard Option A: Traffic Router

*Domain*: Graph Algorithms

Debug a sophisticated Dijkstra-based routing system that accounts for traffic conditions, tolls, and fuel requirements.

*What You'll Do:*
- Fix strategically placed bugs (some are decoys!)
- Handle bidirectional graph traversal
- Implement correct cost calculations with traffic penalties
- Manage fuel station constraints
- Debug algorithmic edge cases

*Skills Tested:*
- Dijkstra's algorithm deep understanding
- Graph algorithms
- Edge case handling
- Distinguishing real bugs from intentional code

---

#### Hard Option B: KV-Cached Multi-Head Attention Debugger

*Domain*: Transformers & Deep Learning

Debug a complex multi-head attention implementation with KV-caching for autoregressive generation - the core mechanism behind modern LLMs.

*What You'll Do:*
- Fix bugs in tensor operations across multiple dimensions
- Correct mathematical formulas (scaling factors, softmax dimensions)
- Handle cache management for efficient inference
- Debug causal masking logic

*Skills Tested:*
- Transformer architecture understanding
- Multi-dimensional tensor operations
- Cache management in autoregressive models
- Mathematical precision in ML implementations
- PyTorch tensor debugging

---

#### Hard Option C: NanoGrad Autograd Engine

*Domain*: Core Deep Learning

Debug a from-scratch automatic differentiation engine - the core technology behind all modern deep learning frameworks like PyTorch and TensorFlow.

*What You'll Do:*
- Fix gradient computation for basic operations (add, multiply, power)
- Correct topological sorting for backpropagation
- Debug the chain rule implementation
- Handle gradient accumulation and zeroing
- Fix neural network training loop

*Skills Tested:*
- Automatic differentiation principles
- Calculus (chain rule, partial derivatives)
- Computational graph algorithms
- Backpropagation understanding
- Core deep learning fundamentals

---

## General Rules

1. *No Solution Sharing*: Do not share solutions with other participants
2. *AI Tools Allowed*: You may use AI assistants, but challenges are designed to resist them
3. *Time Limits*: Each round has a strict time limit - manage your time wisely
4. *Partial Credit*: You don't need to fix everything to score points
5. *Minimal Fixes*: Only fix bugs - don't refactor or rewrite working code
6. *Testing*: Use provided validators to check your solutions

---

## Evaluation Criteria

### Automatic Scoring (70%)
- Test case pass rate
- Correctness of outputs
- Edge case handling

### Manual Review (30%)
- Number and severity of bugs fixed
- Code quality (no new bugs introduced)
- Clean, targeted fixes
- Understanding demonstrated

---

## Getting Started

1. Clone your assigned challenge repository
2. Read the challenge README thoroughly
3. Understand the codebase before making changes
4. Use the validator to test your fixes
5. Submit before the time limit

---

## Technical Requirements

- Python 3.8+
- Additional requirements per challenge (see individual requirements.txt)

---

## FAQs

*Q: How many bugs are in each challenge?*
A: We don't disclose exact numbers. Finding all bugs is part of the challenge.

*Q: Can I use ChatGPT/Claude/Copilot?*
A: Yes, but these challenges are specifically designed to resist AI tools. Use them strategically, but don't rely on them blindly.

*Q: What if I can't fix all the bugs?*
A: Partial credit is available. Focus on the most critical bugs first - ones that cause test failures.

*Q: Can I rewrite the entire codebase?*
A: No. Only fix bugs with minimal, targeted changes. Don't refactor working code.

*Q: How do I know if my fix is correct?*
A: Run the validator. If tests pass, your fix is likely correct. Some hidden tests exist for final scoring.

*Q: What if the validator crashes?*
A: Check your Python version and dependencies. Ensure you haven't introduced syntax errors.

*Q: Are there expected outputs provided?*
A: For most challenges, no. This is intentional - you cannot reverse-engineer solutions from expected outputs.

*Q: What's the difference between hard challenges?*
A: Each tests different domains (algorithms, ML, core DL) but all are equally challenging and AI-resistant.

*Q: Can I compare my implementation with standard libraries?*
A: Yes! Comparing outputs with known-correct implementations (like PyTorch for the autograd challenge) is a valid debugging strategy.

*Q: What if I'm stuck?*
A: Re-read the README, trace through the code manually, add print statements, and test edge cases. Understanding beats guessing.

*Q: Why are there "decoy bugs"?*
A: To test discernment. Not everything that looks wrong is actually wrong. Part of being a good engineer is knowing what NOT to change.

*Q: Will I lose points for "fixing" decoys?*
A: You may break working functionality and fail tests. Only fix actual bugs.

*Q: Can I use external libraries?*
A: For Easy challenge, yes. Medium and Hard challenges should use only the specified dependencies.

*Q: Can I skip a challenge?*
A: Yes! Focus on challenges where you can score maximum points.

*Q: What if I get stuck?*
A: Move to another challenge and come back if time permits. Partial credit is available.

---

## Tips for Success

### Do's
- Read the entire README for each challenge
- Test your code frequently with the validator
- Use debugging prints to trace issues
- Manage your time across all challenges
- Understand the code before changing it

### Don'ts
- Don't refactor working code unnecessarily
- Don't make random changes hoping they work
- Don't spend all time on one challenge
- Don't blindly trust AI suggestions
- Don't "fix" code that looks suspicious but isn't broken

---

## What You'll Learn

- *Algorithms: A, Dijkstra's, pathfinding, graph traversal
- *Debugging*: Systematic bug hunting in complex code
- *Deep Learning*: Autograd, transformers, attention mechanisms
- *Problem Solving*: Breaking down complex problems
- *Discernment*: Knowing what to change and what to leave alone

---

## Contact & Support

For technical issues during the event, contact the organizing team.

---

> "Debugging is like being a detective in a crime movie where you are also the murderer." - Filipe Fortes

---

*Good luck, and may your code be bug-free!*

AI CODEFIX 2025 - Where Real Skills Shine
