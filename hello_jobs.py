# Save 5 fake job listings to jobs.csv

import csv

jobs = [
    ("Senior Software Engineer", "TechCorp Inc."),
    ("Data Scientist", "Analytics Pro"),
    ("UX Designer", "Creative Solutions"),
    ("DevOps Engineer", "Cloud Systems Ltd."),
    ("Product Manager", "Innovation Labs"),
]

with open("jobs.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Job Title", "Company"])
    for title, company in jobs:
        writer.writerow([title, company])

print("Jobs saved to jobs.csv")
