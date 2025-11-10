from pathlib import Path
import random
from typing import Any, Dict, List, Tuple
import yaml
import re

from Core.Repository.database import DatabaseRepository


class Helper:
    @staticmethod
    def load_config(path: Path):
        with open(path, "r") as file:
            return yaml.safe_load(file)

    @staticmethod
    def save_db_file(path: Path, file: Any):
        with open(path, "wb") as f:
            f.write(file.getbuffer())
    
    @staticmethod
    def create_dummy_data(db: DatabaseRepository):
        tables = [
            """
                CREATE TABLE IF NOT EXISTS teacher (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    subject TEXT
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS class (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    teacher_id INTEGER,
                    FOREIGN KEY (teacher_id) REFERENCES teacher(id)
                );
            """,
            """
                CREATE TABLE IF NOT EXISTS student (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    marks INTEGER,
                    class_id INTEGER,
                    FOREIGN KEY (class_id) REFERENCES class(id)
                );
            """,
        ]

        for table in tables:
            db.obj.execute(table)

        # Predefined Student Names
        first_names = [
            "John",
            "Emma",
            "Michael",
            "Sophia",
            "James",
            "Olivia",
            "William",
            "Ava",
            "Daniel",
            "Mia",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Miller",
            "Davis",
            "Garcia",
            "Rodriguez",
            "Wilson",
        ]

        # Predefined class subjects
        class_names = [
            "Mathematics",
            "Data Science",
            "Physics",
            "Chemistry",
            "Biology",
            "Computer Science",
            "Economics",
            "English Literature",
            "History",
            "Psychology",
        ]

        # Distinct teacher names
        teacher_names = [
            "Prof. Alan Turing",
            "Prof. Grace Hopper",
            "Prof. Albert Einstein",
            "Prof. Marie Curie",
            "Prof. Charles Darwin",
            "Prof. Donald Knuth",
            "Prof. Adam Smith",
            "Prof. William Shakespeare",
            "Prof. Herodotus",
            "Prof. Sigmund Freud",
        ]

        # Insert teachers (1-to-1 mapping with classes)
        teachers = [
            (i + 1, teacher_names[i], class_names[i]) for i in range(len(class_names))
        ]
        db.obj.execute(
            "INSERT INTO teacher (id, name, subject) VALUES (%s, %s, %s)",
            teachers
        )

        # Insert classes (map to teachers by ID)
        classes = [(i + 1, class_names[i], i + 1) for i in range(len(class_names))]
        db.obj.execute(
            "INSERT INTO class (id, name, teacher_id) VALUES (%s, %s, %s)",
            classes
        )

        # Insert 1000 students
        students = []
        for i in range(1000):
            student_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            marks = random.randint(35, 100)
            class_id = random.randint(1, len(class_names))
            students.append((i + 1, student_name, marks, class_id))

        db.obj.execute(
            "INSERT INTO student (id, name, marks, class_id) VALUES (%s, %s, %s, %s)",
            students
        )

    @staticmethod
    def schema_to_text(schema: Dict[str, Dict]) -> List[str]:
        chunks = []
        for table, info in schema.items():
            table_desc = f"Table: {table}\nColumns:\n"
            for col in info["columns"]:
                col_desc = f"- {col['name']} ({col['type']})"
                if col["pk"]:
                    col_desc += " [PRIMARY KEY]"
                if col["notnull"]:
                    col_desc += " NOT NULL"
                if col["default"]:
                    col_desc += f" DEFAULT {col['default']}"
                table_desc += col_desc + "\n"

            if info["foreign_keys"]:
                table_desc += "Foreign Keys:\n"
                for fk in info["foreign_keys"]:
                    table_desc += (
                        f"- {fk['from']} → {fk['to_table']}({fk['to_column']})\n"
                    )

            chunks.append(table_desc.strip())
        return chunks

    @staticmethod
    def check_for_unsafe_keywords(query:str) -> bool:
        """Returns True if any unsafe keywords are found."""
        
        UNSAFE_KEYWORDS_REGEX = r"\b(ALTER|CREATE|DELETE|DROP|INSERT|REPLACE|UPDATE|TRUNCATE|GRANT|REVOKE)\b"
        if re.search(UNSAFE_KEYWORDS_REGEX, query, re.IGNORECASE):
            return True
        return False