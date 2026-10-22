import unittest
from engine.runner import run_foxvc_code
from engine.shelf import fox_db_open, fox_db_execute, fox_db_query, fox_db_close

class TestFoxVCDatabase(unittest.TestCase):
    def test_database_shelf_primitives(self):
        db = fox_db_open(":memory:")
        self.assertEqual(db["ok"], 1)

        # Create table
        create_res = fox_db_execute(db, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, score INTEGER)")
        self.assertEqual(create_res["ok"], 1)

        # Insert records
        ins1 = fox_db_execute(db, "INSERT INTO users (name, score) VALUES (?, ?)", ["Alice", 100])
        self.assertEqual(ins1["ok"], 1)
        self.assertEqual(ins1["last_id"], 1)

        ins2 = fox_db_execute(db, "INSERT INTO users (name, score) VALUES (?, ?)", ["Bob", 85])
        self.assertEqual(ins2["ok"], 1)
        self.assertEqual(ins2["last_id"], 2)

        # Query records
        rows = fox_db_query(db, "SELECT * FROM users ORDER BY score DESC")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Alice")
        self.assertEqual(rows[0]["score"], 100)
        self.assertEqual(rows[1]["name"], "Bob")
        self.assertEqual(rows[1]["score"], 85)

        # Close
        close_res = fox_db_close(db)
        self.assertEqual(close_res, 1)

    def test_foxvc_script_database_execution(self):
        code = """db = dbOpen(":memory:")
dbExecute(db, "CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT)")
dbExecute(db, "INSERT INTO items (title) VALUES ('FoxVC')")
rows = dbQuery(db, "SELECT title FROM items")
first_item = rows[0]
say "DB Item: " + first_item.title
dbClose(db)
"""
        res = run_foxvc_code(code)
        self.assertTrue(res["success"], f"Script failed: {res.get('error')}")
        self.assertIn("DB Item: FoxVC", res["output"])

if __name__ == "__main__":
    unittest.main()
