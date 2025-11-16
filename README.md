# Steerable Approximate Query Processing (AQP) Engine

This project is a web-based prototype of a "steerable" Approximate Query Processing (AQP) system. It allows users to run aggregate queries (`AVG`, `SUM`, `COUNT`) on a massive dataset (the NYC Taxi trip data) and interactively refine the accuracy of the result in real-time, demonstrating a human-in-the-loop approach to big data analytics.

Instead of waiting minutes for an exact answer, a user gets an immediate, rough estimate. They can then "steer" the query by clicking "Refine," which processes more data and updates the answer, allowing them to stop as soon as the result is good enough for their needs.

<img width="907" height="818" alt="image" src="https://github.com/user-attachments/assets/d6722ac4-ff1c-498c-93aa-ad588783ce32" />

<img width="907" height="818" alt="image" src="https://github.com/user-attachments/assets/f56bf2dd-b65c-4dcc-aa09-596f7d3fcb6f" />

**Detailed Report:** [Click here!](https://docs.google.com/document/d/1c0VTkjij0tspyLQBh16UOjzi99aiyNCnOoZ6dX23LdA/edit?usp=sharing)

## Features

- Interactive Steering: Start with a fast, rough estimate and click "Refine" to progressively increase accuracy.
- Multiple Aggregates: Supports `AVG`, `SUM`, and `COUNT` aggregates.
- Dynamic Column Selection: Lets the user choose which data column to analyze (`fare_amount`, `trip_distance`, `passenger_count`).
- Live Data Streaming: Pulls data directly from the NYC OpenData Socrata API in chunks. No download or local data files required.
- Real-time Visualization: A live-updating line chart shows the aggregate value converging as more data is processed.
- Confidence Intervals: For `AVG` queries, the system displays the 95% confidence interval, which narrows with each refinement.

## Methodology

### From File Blocks to API Streaming

This implementation represents an evolution from the project's initial planning (as documented in the [Report](https://docs.google.com/document/d/1c0VTkjij0tspyLQBh16UOjzi99aiyNCnOoZ6dX23LdA/edit?usp=sharing)).

- Initial Plan: The original plan was to perform offline pre-processing: download the entire 13GB+ dataset, shuffle it, and partition it into thousands of small, static block files (e.g., `block_001.csv`).
- Final Implementation: We quickly identified that this approach was impractical for a real-world scenario. The dataset is too large to download, and the static files cannot handle dynamically updating data—a key limitation we noted in our report.
- The Solution: This project implements a live streaming method. The Socrata API for the dataset allows for pagination using `limit` and `offset` parameters. We use this feature as a "virtual partitioning" system.

### Why this preserves the core idea:

The "block" is a conceptual unit of work. The core idea of "block partitioning" is to have a set of sequential, bite-sized data chunks that the system can process one by one.

- In the old plan, a "block" was a physical file (e.g., `block_002.csv`).
- In this implementation, a "block" is an API page (e.g., `limit=10000 & offset=10000`).

The "Refine" button does the exact same job in both systems: it tells the backend to fetch and process the next sequential block. This API-based approach is more efficient, requires zero setup, and directly solves the problem of dynamic data, aligning perfectly with the advanced goals of the project.

## How It Works

The system is built on a simple, decoupled frontend/backend architecture:

### Backend (`main.py`)

- A Python server using **FastAPI** that acts as the query engine.
- It maintains a `QueryState` in memory to track the `running_sum`, `running_count`, `running_sum_sq`, and API offset.
- `/start_query`: Resets the state, fetches the first chunk of data from the Socrata API, and returns the first estimate.
- `/refine_query`: Fetches the next chunk of data, merges it with the existing state, and returns the updated estimate.

### Frontend (`index.html`)

- A single, dependency-free HTML file with vanilla JavaScript.
- Uses Chart.js to visualize the results.
- Provides a UI with dropdowns to select the aggregate and column.
- The "Start Over" button calls `/start_query` and clears the chart.
- The "Refine" button calls `/refine_query` and appends the new data point to the chart, showing the trend.

## How to Run This Project

### Prerequisites
- Python 3.7+
- A web browser (Chrome, Firefox, etc.)

### Backend Setup (Terminal)

#### Clone the repository:
```sh
git clone https://github.com/anij715/Steerable-Approximate-Query-Processing-AQP.git
cd Steerable-Approximate-Query-Processing-AQP
```

#### Create and activate a virtual environment:

1. Windows:
```sh
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. macOS / Linux:
```sh
python3 -m venv venv
source venv/bin/activate
```

#### Install the required packages:
_(A `requirements.txt` file is provided in this repository)_

```sh
pip install -r requirements.txt
```

#### Run the backend server:
```sh
uvicorn main:app --reload
```

Your server is now running at `http://127.0.0.1:8000`. Leave this terminal open.

### Frontend Setup (Browser)

- Navigate to the project folder in your file explorer.
- Double-click the `index.html` file.
- It will open in your default web browser and automatically connect to the running backend. You can now use the application.
