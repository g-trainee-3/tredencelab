"""
Parameterised SQL queries for Mergington Activities database.

All queries use psycopg2-style %s placeholders for safe parameterised queries.
No string formatting or SQL injection vulnerabilities.
"""

SQL_QUERIES = {
    "q1": {
        # How many students have signed up for Chess Club?
        "sql": """
            SELECT COUNT(*) FROM signups 
            WHERE activity_id = (SELECT id FROM activities WHERE name = %s)
        """,
        "params": ("Chess Club",)
    },
    
    "q2": {
        # List all activities that still have spots available.
        "sql": """
            SELECT a.id, a.name, a.description, a.max_participants, a.schedule 
            FROM activities a 
            WHERE a.max_participants > (
                SELECT COUNT(*) FROM signups s 
                WHERE s.activity_id = a.id
            )
            ORDER BY a.name
        """,
        "params": ()
    },
    
    "q3": {
        # Which activities is student Alice Johnson signed up for?
        "sql": """
            SELECT a.id, a.name, a.description, a.max_participants, a.schedule 
            FROM activities a 
            JOIN signups s ON a.id = s.activity_id 
            WHERE s.student_name = %s
            ORDER BY a.name
        """,
        "params": ("Alice Johnson",)
    },
    
    "q4": {
        # Show activities with more than 10 max participants.
        "sql": """
            SELECT id, name, description, max_participants, schedule 
            FROM activities 
            WHERE max_participants > %s
            ORDER BY max_participants DESC
        """,
        "params": (10,)
    },
    
    "q5": {
        # Remove Alice Johnson from Basketball Team.
        "sql": """
            DELETE FROM signups 
            WHERE activity_id = (
                SELECT id FROM activities WHERE name = %s
            ) 
            AND student_name = %s
        """,
        "params": ("Basketball Team", "Alice Johnson")
    }
}


if __name__ == "__main__":
    # Print queries for verification
    for key, query_dict in SQL_QUERIES.items():
        print(f"\n{key}:")
        print(f"  SQL: {query_dict['sql'].strip()}")
        print(f"  Params: {query_dict['params']}")
