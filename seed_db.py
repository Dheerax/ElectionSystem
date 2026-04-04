import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = 'election.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed():
    print("Seeding database with quality sample data...")
    db = get_db()
    
    # Enable foreign keys
    db.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Clear existing data to start fresh (optional, but good for a clean seed)
    tables = ['votes', 'complaints', 'admin_log', 'candidates', 'election_eligible_depts', 'election_eligible_rolls', 'elections', 'voters']
    for t in tables:
        db.execute(f"DELETE FROM {t};")
    
    # Reset auto increments
    db.execute("DELETE FROM sqlite_sequence;")
    
    # 2. Insert Elections
    now = datetime.now()
    
    active_start = (now - timedelta(days=2)).strftime('%Y-%m-%d')
    active_end   = (now + timedelta(days=5)).strftime('%Y-%m-%d')
    
    upcoming_start = (now + timedelta(days=10)).strftime('%Y-%m-%d')
    upcoming_end   = (now + timedelta(days=15)).strftime('%Y-%m-%d')
    
    ended_start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    ended_end   = (now - timedelta(days=25)).strftime('%Y-%m-%d')
    
    elections = [
        ("Student Council President 2026", active_start, active_end, "President", "department", "", ""),
        ("Dept Rep - CSE(AI)", upcoming_start, upcoming_end, "Representative", "department", "", ""),
        ("Sports Secretary By-Election", ended_start, ended_end, "Sports Secretary", "department", "", "")
    ]
    
    election_ids = []
    for e in elections:
        cur = db.execute(
            "INSERT INTO elections(election_title, start_date, end_date, position_role, eligible_type, roll_start, roll_end) VALUES(?,?,?,?,?,?,?)",
            e
        )
        election_ids.append(cur.lastrowid)
        
    # Insert Eligibilities
    for dept in ["CSE", "CSE-AI", "ECE", "ME", "CE", "EEE"]:
        db.execute("INSERT INTO election_eligible_depts(election_id, department) VALUES(?,?)", (election_ids[0], dept))
    db.execute("INSERT INTO election_eligible_depts(election_id, department) VALUES(?,?)", (election_ids[1], "CSE-AI"))
    for dept in ["CSE", "CSE-AI", "ECE", "ME", "CE", "EEE"]:
        db.execute("INSERT INTO election_eligible_depts(election_id, department) VALUES(?,?)", (election_ids[2], dept))
    
    # 3. Insert Candidates
    # Election 1 (Active)
    db.execute("INSERT INTO candidates(election_id, candidate_name, position, party_name, description) VALUES(1, 'Aarav Sharma', 'President', 'Progressive Alliance', 'Current VP of the Cultural Committee. Led 3 major campus events last year.')")
    db.execute("INSERT INTO candidates(election_id, candidate_name, position, party_name, description) VALUES(1, 'Priya Patel', 'President', 'Student Voice', 'Topper of CSE-AI 2023 batch. Advocates for better lab facilities and academic resources.')")
    db.execute("INSERT INTO candidates(election_id, candidate_name, position, party_name, description) VALUES(1, 'Rohan Desai', 'President', 'Independent', 'Independent candidate with 2 years experience in student welfare initiatives and sports management.')")
    
    # Election 2 (Upcoming)
    db.execute("INSERT INTO candidates(election_id, candidate_name, position, party_name, description) VALUES(2, 'Aditya Singh', 'Dept Rep', 'Tech Innovators', 'Core member of the Coding Club. Organized multiple hackathons and placement drives.')")
    db.execute("INSERT INTO candidates(election_id, candidate_name, position, party_name, description) VALUES(2, 'Neha Gupta', 'Dept Rep', 'Builders Bloc', 'Project lead on the Smart Campus IoT initiative. Passionate about bridging students and faculty.')")
    
    # Election 3 (Ended)
    db.execute("INSERT INTO candidates(election_id, candidate_name, position, party_name, description) VALUES(3, 'Karan Malhotra', 'Sports Sec', 'Athletics First', 'State-level cricket player. Wants to revive the intercollegiate sports calendar.')")
    db.execute("INSERT INTO candidates(election_id, candidate_name, position, party_name, description) VALUES(3, 'Sneha Reddy', 'Sports Sec', 'All Rounders', 'National-level badminton player and fitness enthusiast. Focused on inclusive sports participation.')")
    
    # 4. Insert Voters
    first_names = ["Rahul", "Anjali", "Vikram", "Pooja", "Arjun", "Kritika", "Deepak", "Riya", "Sanjay", "Ananya"]
    last_names = ["Kumar", "Sharma", "Singh", "Verma", "Jain", "Mehta", "Bose", "Nair", "Rao", "Das"]
    depts = ["CSE", "ECE", "ME", "CE", "CSE-AI"]
    
    voters_inserted = 0
    # CSE 2023 Batch for active
    for i in range(1, 51):
        roll = f"23G01A32{i:02d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        dept = "CSE"
        is_registered = 1 if random.random() > 0.1 else 0
        has_voted = 0
        db.execute(
            "INSERT INTO voters(roll_number, name, department, email, phone, photo, is_registered, has_voted) VALUES(?,?,?,?,?,?,?,?)",
            (roll, name, dept, f"{name.split()[0].lower()}.{roll.lower()}@gmail.com", f"9{random.randint(100000000, 999999999)}", "data:image/png;base64,mock", is_registered, has_voted)
        )
        voters_inserted += 1
        
    # CSE-AI 2024 Batch for upcoming
    for i in range(1, 31):
        roll = f"24G01A43{i:02d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        dept = "CSE-AI"
        is_registered = 1 if random.random() > 0.2 else 0
        db.execute(
            "INSERT INTO voters(roll_number, name, department, email, phone, photo, is_registered, has_voted) VALUES(?,?,?,?,?,?,?,?)",
            (roll, name, dept, f"{name.split()[0].lower()}.{roll.lower()}@gmail.com", f"8{random.randint(100000000, 999999999)}", "data:image/png;base64,mock", is_registered, 0)
        )
        voters_inserted += 1
        
    # ME 2022 Batch
    for i in range(1, 21):
        roll = f"22G01A12{i:02d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        dept = "ME"
        db.execute(
            "INSERT INTO voters(roll_number, name, department, is_registered, has_voted) VALUES(?,?,?,?,?)",
            (roll, name, dept, 1, 0)
        )
        voters_inserted += 1

    # Insert explicit test user requested by user
    db.execute(
        "INSERT INTO voters(roll_number, name, department, email, phone, is_registered, has_voted) VALUES(?,?,?,?,?,?,?)",
        ("22G01A4321", "Test Student", "CSE-AI", "test.22g01a4321@gmail.com", "9998887771", 0, 0)
    )
        
    # 5. Insert Votes
    active_voters_res = db.execute("SELECT voter_id FROM voters WHERE roll_number LIKE '23G01A32%' AND is_registered=1").fetchall()
    active_voters = [v['voter_id'] for v in active_voters_res]
    
    for vid in random.sample(active_voters, int(len(active_voters) * 0.7)):
        cid = random.choice([1, 2, 3])
        ts = (datetime.now() - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))).isoformat()
        db.execute(
            "INSERT INTO votes(voter_id, candidate_id, election_id, ip_address, location, timestamp) VALUES(?,?,?,?,?,?)",
            (vid, cid, 1, "192.168.1.100", "Campus WiFi", ts)
        )
        db.execute("UPDATE voters SET has_voted=1 WHERE voter_id=?", (vid,))
        
    old_voters_res = db.execute("SELECT voter_id FROM voters WHERE roll_number LIKE '22G01A12%' AND is_registered=1").fetchall()
    old_voters = [v['voter_id'] for v in old_voters_res]
    for vid in random.sample(old_voters, int(len(old_voters) * 0.8)):
        cid = random.choice([6, 7])
        ts = (datetime.now() - timedelta(days=28)).isoformat()
        db.execute(
            "INSERT INTO votes(voter_id, candidate_id, election_id, ip_address, location, timestamp) VALUES(?,?,?,?,?,?)",
            (vid, cid, 3, "192.168.1.105", "Hostel Network", ts)
        )
        
    # 6. Insert Complaints
    complaints = [
        ("Rahul Kumar", "23G01A3201", "My name is misspelled in the voter list. It should be Rahul Kumar, not Rahul Kumae. Please fix this.", "pending"),
        ("Anjali Sharma", "24G01A4315", "I am unable to see the department rep election on my dashboard even though my roll number is eligible.", "pending"),
        ("Vikram Singh", "22G01A1211", "The system kicked me out while capturing the photo. Now it says registered but I didn't get an email.", "resolved"),
        ("Pooja Verma", "23G01A3242", "I lost my ID card, can I upload fee receipt instead for complaint verification? Trying to report an issue.", "rejected")
    ]
    
    for c in complaints:
        db.execute(
            "INSERT INTO complaints(name, roll_number, description, status) VALUES(?,?,?,?)",
            c
        )
        
    # 7. Insert Admin Logs
    logs = [
        ("Created Election: Student Council President 2026", "Elections", (datetime.now() - timedelta(days=3)).isoformat()),
        ("Imported 100 voters via CSV", "Voters", (datetime.now() - timedelta(days=2, hours=5)).isoformat()),
        ("Added Candidate: Aarav Sharma", "Candidates", (datetime.now() - timedelta(days=2, hours=4)).isoformat()),
        ("Added Candidate: Priya Patel", "Candidates", (datetime.now() - timedelta(days=2, hours=3)).isoformat()),
        ("Added Candidate: Rohan Desai", "Candidates", (datetime.now() - timedelta(days=2, hours=2)).isoformat()),
        ("Resolved Complaint #3", "Complaints", (datetime.now() - timedelta(hours=5)).isoformat()),
    ]
    
    for l in logs:
        db.execute("INSERT INTO admin_log(action, target, timestamp) VALUES(?,?,?)", l)
        
    db.commit()
    db.close()
    print("Database seeded successfully with realistic data!")

if __name__ == '__main__':
    seed()
