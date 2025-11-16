import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests 

CHUNK_SIZE = 10000 
API_ENDPOINT = "https://data.cityofnewyork.us/resource/t7ny-aygi.json"

app = FastAPI(
    title="Steerable AQP Engine",
    description="A simple API for interactive, progressive query processing."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

class QueryState:
    def __init__(self):
        self.current_offset = 0 
        self.running_sum = 0.0
        self.running_count = 0
        self.running_sum_sq = 0.0 
        self.is_done = False 
        self.column_to_query = None 
        self.aggregate_function = None

    def reset(self):
        self.current_offset = 0 
        self.running_sum = 0.0
        self.running_count = 0
        self.running_sum_sq = 0.0
        self.is_done = False 
        self.column_to_query = None 
        self.aggregate_function = None

query_state = QueryState()

class StartQueryRequest(BaseModel):
    column_name: str
    aggregate_function: str

class QueryResult(BaseModel):
    average: float
    confidence_interval: float
    percent_complete: float
    is_done: bool

def calculate_statistics():
    """Calculates the current statistics based on the global state."""

    if query_state.running_count == 0:
        return 0.0, 0.0, 0.0, False 

    is_done = query_state.is_done
    records_processed = query_state.running_count
    
    agg_func = query_state.aggregate_function
    
    if agg_func == "AVG":
        avg = query_state.running_sum / query_state.running_count

        # Calculate 95% Confidence Interval
        variance = (query_state.running_sum_sq / query_state.running_count) - (avg ** 2)
        if variance < 0: variance = 0 
            
        std_dev = np.sqrt(variance)
        std_error = std_dev / np.sqrt(query_state.running_count)
        confidence_interval = 1.96 * std_error

        return avg, confidence_interval, records_processed, is_done
        
    elif agg_func == "SUM":
        # SUM is an exact running total, so CI is 0
        return query_state.running_sum, 0, records_processed, is_done
        
    elif agg_func == "COUNT":
        # COUNT is an exact running total, so CI is 0
        return query_state.running_count, 0, records_processed, is_done
        
    else:
        # Default case / error
        return 0.0, 0.0, 0.0, is_done

def fetch_next_chunk():
    """Fetches the next chunk of data from the Socrata API."""
    if query_state.is_done or not query_state.column_to_query:
        return False 

    col = query_state.column_to_query 
    
    # If we're just counting, we don't need the column value,
    # but we still need to filter by it.
    # The SODA API is simple, so we'll just fetch the column
    # anyway, as it's needed for SUM and AVG.
    
    soda_query = (
        f"?$select={col}"
        f"&$where={col} > 0"
        f"&$limit={CHUNK_SIZE}"
        f"&$offset={query_state.current_offset}"
    )
    
    api_url = API_ENDPOINT + soda_query
    
    print(f"Fetching: {api_url}")

    try:
        response = requests.get(api_url)
        response.raise_for_status() 
        data = response.json()
        
        if not data:
            query_state.is_done = True
            print("API returned no more data. Query is complete.")
            return False
        # We *always* need the count
        query_state.running_count += len(data)
        
        # We only need to do math for SUM and AVG
        if query_state.aggregate_function in ["SUM", "AVG"]:
            for record in data:
                try:
                    value = float(record[col])
                    query_state.running_sum += value
                    # Only calculate sum_sq if we're doing AVG
                    if query_state.aggregate_function == "AVG":
                        query_state.running_sum_sq += (value ** 2)
                
                except (KeyError, ValueError, TypeError):
                    continue 
                
        query_state.current_offset += CHUNK_SIZE
        return True 

    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed: {e}")
        query_state.is_done = True 
        return False

@app.post("/start_query", response_model=QueryResult)
def start_query(request: StartQueryRequest):
    """
    Resets the query state and returns the result from the *first* block.
    """
    query_state.reset()

    query_state.column_to_query = request.column_name 
    query_state.aggregate_function = request.aggregate_function
    
    fetch_next_chunk() 
    avg, ci, count, done = calculate_statistics() 
    return {"average": avg, "confidence_interval": ci, "percent_complete": count, "is_done": done}

@app.post("/refine_query", response_model=QueryResult)
def refine_query():
    """
    Processes the *next* chunk from the API.
    (No changes needed here, as it uses the saved state)
    """
    fetch_next_chunk() 
    avg, ci, count, done = calculate_statistics() 
    return {"average": avg, "confidence_interval": ci, "percent_complete": count, "is_done": done}

@app.get("/")
def read_root():
    return {"message": "Steerable AQP server is running. See /docs for API documentation."}