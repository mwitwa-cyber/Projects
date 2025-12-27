from mcp.server.fastmcp import FastMCP
import pandas as pd
import sqlite3
import os

# Initialize the Server
mcp = FastMCP("Persistent-Financial-Analyst")

# Define the Persistence Path - Crucial for preventing data loss
DATA_DIR = "/data"

@mcp.tool()
def analyze_market_csv(filename: str) -> str:
    """
    Reads a CSV file from the persistent volume and returns a statistical summary.
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return f"Error: File {filename} not found in persistent storage."
    
    try:
        df = pd.read_csv(filepath)
        summary = df.describe().to_string()
        return f"Analysis of {filename}:\n{summary}"
    except Exception as e:
        return f"Analysis Failed: {str(e)}"

@mcp.tool()
def log_trade_idea(symbol: str, strategy: str) -> str:
    """
    Saves a trade idea to the persistent SQLite database.
    This data survives workspace deletions.
    """
    db_path = os.path.join(DATA_DIR, 'trade_journal.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS ideas 
                      (symbol TEXT, strategy TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    cursor.execute("INSERT INTO ideas (symbol, strategy) VALUES (?,?)", (symbol, strategy))
    conn.commit()
    conn.close()
    return f"Successfully logged strategy for {symbol}."

if __name__ == "__main__":
    mcp.run()
