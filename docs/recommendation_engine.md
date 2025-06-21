# 🧠 Recommendation Engine Design

This document outlines the architecture and strategy for building the content-based recommendation engine for the Open Source Together platform.

## 1. Core Objective

The primary goal is to provide users with highly relevant project recommendations. Instead of relying on simple popularity metrics, the engine will analyze the **content and characteristics** of projects to identify substantive similarities.

## 2. Recommendation Strategy: Content-Based Filtering

We will implement a **Content-Based Filtering** system. This approach is based on a simple but powerful principle:

> "If a user shows strong interest in a project, they will likely be interested in other projects that are fundamentally similar in content."

### Strong Interest Signals

We will determine user interest based on concrete, high-effort actions rather than passive "likes". The primary signals are:
-   **`TeamMember`**: The user is a member of the project's team.
-   **`Contribution`**: The user has contributed code, design, or documentation.
-   **`Application`**: The user has applied to join the project.

## 3. Machine Learning Workflow

The process will follow a standard ML pipeline, which can be encapsulated within a `RecommendationService` in the `src/infrastructure/analysis/` directory.

### Step 1: Feature Engineering (Vectorization)

We must convert project data into a numerical format (vectors) that a machine can understand.

-   **Textual Data (`description`, `readme`):**
    -   **Technique:** TF-IDF (`Term Frequency-Inverse Document Frequency`).
    -   **Purpose:** To identify the most uniquely descriptive words for each project, giving them more weight.

-   **Categorical Data (`language`, `topics`):**
    -   **Technique:** One-Hot Encoding.
    -   **Purpose:** To convert each category (like "Python" or "fintech") into a binary feature.

The combination of these techniques will result in a single, comprehensive vector for each project.

### Step 2: Similarity Calculation

Once all projects are represented as vectors, we will compute their similarity.

-   **Technique:** Cosine Similarity.
-   **Purpose:** To calculate a similarity score (from -1 to 1) between every pair of projects. A score closer to 1 indicates a higher degree of similarity.

The result of this step will be a **project-project similarity matrix**.

### Step 3: Generating Recommendations

With the similarity matrix, providing recommendations is efficient:

1.  **Build User Profile**: For a given user, compile a profile of their "strong interest" projects (from `TeamMember`, `Contribution`, `Application`).
2.  **Find Similar Projects**: Look up these projects in the similarity matrix.
3.  **Aggregate & Rank**: Aggregate the similarity scores to find the projects that are most similar to the user's overall interest profile, and recommend the top-ranked ones.

## 4. Technical Stack

-   **Data Manipulation**: `pandas`
-   **ML Modeling**: `scikit-learn` (for TF-IDF, One-Hot Encoding, and Cosine Similarity)
-   **Database Interaction**: `SQLAlchemy` 