from fastapi import FastAPI
from pydantic import BaseModel ,Field
from datetime import date
import uuid
import sqlite3
import logging

logging.basicConfig(
    filename="train.log",
    level=logging.WARNING,
    format="%(asctime)s, | %(levelname)s | %(message)s"
                )

app = FastAPI()

DB_FILE = "train.db"

def create_tables():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training(
            response_id TEXT PRIMARY KEY,
            employee_id TEXT,
            name TEXT,
            trainer_name TEXT,
            training_topic TEXT,
            training_duration REAL,
            description TEXT,
            training_date TEXT,
            FOREIGN KEY(employee_id)
            REFERENCES employee(employee_id)
                   )
        
        """)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee(
    employee_id TEXT PRIMARY KEY,
    employee_name TEXT,
    department TEXT,
    designation TEXT,
    email TEXT
    )
    """)

    conn.commit()
    conn.close()


create_tables()


class training_data(BaseModel):
    employee_id:str = Field(...,min_length=6,max_length=6)
    name : str = Field(...,min_length=3,max_length=30)
    trainer_name: str = Field(...,min_length=3,max_length=30)
    topic : str = Field(...,min_length=1,max_length=100)
    duration : float = Field(...,gt=0.1 , lt= 9)
    description : str = Field(...,min_length=1,max_length=1500)
    training_date: date

class Employee(BaseModel):
    employee_id:str = Field(...,min_length=6,max_length=6)
    employee_name: str = Field(..., min_length=5,max_length=30)
    department: str = Field(...,min_length=5, max_length=20)
    designation: str = Field(...,min_length=2, max_length=20)
    email: str = Field(...,min_length=5, max_length=50)

@app.post("/add_training")
def create_training_sheet(payload:training_data):
    unique_response_id = str(uuid.uuid4())

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
            INSERT INTO training(
                   employee_id,
                   response_id,
                   name,
                   trainer_name,
                   training_topic,
                   training_duration,
                   description,
                   training_date) VALUES (?,?, ?, ?, ?, ?, ?, ?)
    """,
    (   
        payload.employee_id,
        unique_response_id,
        payload.name,
        payload.trainer_name,
        payload.topic,
        payload.duration,
        payload.description,
        str(payload.training_date)
    ))
    
    conn.commit()
    conn.close()

    logging.warning(f"New Response Recorded with response id {unique_response_id}")
    return{
        "message" : f"Data Updated successfully with response id {unique_response_id}"
    }

@app.get("/result/{response_id}")
def get_training(response_id: str):

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM training WHERE response_id=?",
        (response_id,)
    )

    record = cursor.fetchone()

    conn.close()

    if not record:
        return {"message": "Record not found"}
    logging.warning(f"Data fetch for response id {response_id}")
    return record

@app.delete("/delete_training/{response_id}")
def delete_trainingdata(response_id: str):

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM training WHERE response_id=?",
        (response_id,)
    )
    conn.commit()
    conn.close()
    logging.info(f"Training Data Deleted : {response_id}")

    return {
        "result": "Training Data Deleted Successfully"
    }


    


@app.post("/newemployee")
def create_employee(payload: Employee):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT employee_id FROM employee WHERE employee_id = ?",
        (payload.employee_id,)
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {
            "error": "Employee ID already exists"
        }

    cursor.execute("""
        INSERT INTO employee(
            employee_id,
            employee_name,
            department,
            designation,
            email
        )
        VALUES (?, ?, ?, ?, ?)
    """,
    (
        payload.employee_id,
        payload.employee_name,
        payload.department,
        payload.designation,
        payload.email
    ))

    conn.commit()
    conn.close()
    logging.warning(f"Employee Data created successfully with emp id {payload.employee_id}")
    return {
        "message": "Employee Data created successfully"
    }

@app.get("/emp_details/{employee_id}")
def get_employee(employee_id: str):

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM employee WHERE employee_id=?",
        (employee_id,)
    )

    record = cursor.fetchone()

    conn.close()

    if not record:
        return {"message": "Record not found"}
    logging.warning(f"Data fetch for employee id {employee_id}")
    return record

@app.delete("/delete_emp/{employee_id}")
def delete_emp(employee_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                    DELETE FROM employee WHERE employee_id=?
                   """,
                   (employee_id,)
                    )
    conn.commit()
    conn.close()
    logging.info(f"Employee Data Deleted : {employee_id}")

    return {
        "result": "Employee Data Deleted Successfully"
    }





@app.get("/employee-training/{employee_id}")
def employee_training(employee_id: str):

    conn = sqlite3.connect(DB_FILE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        employee.employee_id,
        employee.employee_name,
        employee.department,
        employee.designation,
        employee.email,
        training.response_id,
        training.trainer_name,
        training.training_topic,
        training.training_duration,
        training.description,
        training.training_date
    FROM employee 
    LEFT JOIN training 
    ON employee.employee_id = training.employee_id
    WHERE employee.employee_id = ?
    """,
    (employee_id,)
    )

    records = cursor.fetchall()

    conn.close()

    if not records:
        return {"message": "No Record Found"}

    return [dict(row) for row in records]
