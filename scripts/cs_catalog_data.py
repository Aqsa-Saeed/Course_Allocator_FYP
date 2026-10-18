"""
SAMPLE course catalog for the Computer Science department.

None of this is real university data. It is a plausible catalog, written so
that its course requirements use the same vocabulary as the faculty
specializations, which gives the embeddings and ranking something meaningful
to match. Replace it with the real catalog when you have one.

requirements_text is what gets turned into an embedding later, so it
describes the topics taught and the expertise an instructor needs.
"""

PROGRAMS = [
    "BS Computer Science",
    "BS Software Engineering",
    "BS Artificial Intelligence",
]

# code, title, program, credit_hours, requirements_text
COURSES = [
    # --- BS Computer Science ---
    ("CS-101", "Programming Fundamentals", "BS Computer Science", 4,
     "Introductory programming: variables, control flow, functions, arrays and problem solving. Needs an instructor with strong programming fundamentals and experience teaching beginners."),
    ("CS-102", "Object Oriented Programming", "BS Computer Science", 4,
     "Object-oriented programming: classes, inheritance, polymorphism, encapsulation and exceptions. Needs strong programming language expertise."),
    ("CS-201", "Data Structures and Algorithms", "BS Computer Science", 4,
     "Data structures and algorithms: lists, stacks, queues, trees, graphs, sorting, searching and complexity analysis. Needs a strong programming and algorithms background."),
    ("CS-210", "Database Systems", "BS Computer Science", 4,
     "Database systems: relational model, SQL, normalization, transactions, indexing and query processing. Needs database systems expertise."),
    ("CS-220", "Operating Systems", "BS Computer Science", 3,
     "Operating systems: processes, threads, scheduling, memory management, file systems and concurrency. Needs systems and operating systems expertise."),
    ("CS-230", "Computer Networks", "BS Computer Science", 3,
     "Computer networks: network layers, TCP/IP, routing, switching and network protocols. Needs networking expertise."),
    ("CS-310", "Web Engineering", "BS Computer Science", 3,
     "Web engineering: HTML, CSS, JavaScript, server-side development, REST APIs and full stack web development. Needs web development expertise."),
    ("CS-320", "Mobile Application Development", "BS Computer Science", 3,
     "Mobile application development: Android and cross-platform apps, user interfaces, mobile data storage and deployment. Needs mobile application development expertise."),
    ("CS-330", "Information Security", "BS Computer Science", 3,
     "Information security: cryptography, network security, authentication, secure systems, blockchain basics and cybersecurity threats. Needs information security or cybersecurity expertise."),
    ("CS-340", "Internet of Things", "BS Computer Science", 3,
     "Internet of Things: sensors, embedded devices, communication protocols, IoT platforms and applications. Needs Internet of Things and embedded systems expertise."),
    ("CS-350", "Cloud Computing", "BS Computer Science", 3,
     "Cloud computing: virtualization, cloud service models, containers, scalable deployment and cloud platforms. Needs cloud computing expertise."),
    ("CS-360", "Human-Computer Interaction", "BS Computer Science", 3,
     "Human-computer interaction: usability, interface design, user research and evaluation methods. Needs human-computer interaction expertise."),
    ("CS-370", "Digital Image Processing", "BS Computer Science", 3,
     "Image processing: image enhancement, filtering, segmentation, feature extraction and digital image processing techniques. Needs image processing or computer vision expertise."),
    # --- BS Software Engineering ---
    ("SE-201", "Software Engineering", "BS Software Engineering", 3,
     "Software engineering: process models, requirements, design, testing and maintenance. Needs software engineering and project experience."),
    ("SE-310", "Software Quality Assurance", "BS Software Engineering", 3,
     "Software quality assurance: testing strategies, test automation, quality metrics, inspections and quality standards. Needs software quality assurance expertise."),
    ("SE-320", "Software Project Management", "BS Software Engineering", 3,
     "Software project management: planning, estimation, scheduling, risk management and team coordination. Needs software project management expertise."),
    ("SE-340", "DevOps and Continuous Delivery", "BS Software Engineering", 3,
     "DevOps: continuous integration and delivery, version control, containers, deployment automation and monitoring. Needs DevOps and full stack development expertise."),
    # --- BS Artificial Intelligence ---
    ("AI-201", "Artificial Intelligence", "BS Artificial Intelligence", 3,
     "Artificial intelligence: search, knowledge representation, reasoning, planning and intelligent agents. Needs artificial intelligence expertise."),
    ("AI-301", "Machine Learning", "BS Artificial Intelligence", 4,
     "Machine learning: supervised and unsupervised learning, model evaluation, regression, classification and clustering. Needs machine learning expertise."),
    ("AI-310", "Data Science", "BS Artificial Intelligence", 3,
     "Data science: data preparation, exploration, statistical analysis, visualization and predictive modeling. Needs data science and machine learning expertise."),
    ("AI-401", "Deep Learning", "BS Artificial Intelligence", 4,
     "Deep learning: neural networks, convolutional and recurrent networks, optimization and training deep models. Needs deep learning expertise."),
    ("AI-410", "Natural Language Processing", "BS Artificial Intelligence", 3,
     "Natural language processing: text processing, language models, embeddings, sequence modeling and language applications. Needs natural language processing expertise."),
    ("AI-420", "Computer Vision", "BS Artificial Intelligence", 3,
     "Computer vision: image classification, object detection, segmentation and visual recognition with deep learning. Needs computer vision expertise."),
    ("AI-430", "Robotics", "BS Artificial Intelligence", 3,
     "Robotics: robot kinematics, sensing, control, autonomy and embedded robotic systems. Needs robotics and embedded systems expertise."),
]

# (course, prerequisite) — the prerequisite must be taken before the course
PREREQUISITES = [
    ("CS-102", "CS-101"),
    ("CS-201", "CS-102"),
    ("CS-210", "CS-102"),
    ("CS-220", "CS-201"),
    ("CS-230", "CS-201"),
    ("CS-310", "CS-210"),
    ("CS-320", "CS-102"),
    ("CS-330", "CS-230"),
    ("CS-340", "CS-230"),
    ("CS-350", "CS-230"),
    ("CS-360", "CS-102"),
    ("CS-370", "CS-201"),
    ("SE-201", "CS-101"),
    ("SE-310", "SE-201"),
    ("SE-320", "SE-201"),
    ("SE-340", "SE-201"),
    ("AI-201", "CS-201"),
    ("AI-301", "AI-201"),
    ("AI-310", "CS-210"),
    ("AI-401", "AI-301"),
    ("AI-410", "AI-301"),
    ("AI-420", "AI-401"),
    ("AI-430", "AI-201"),
]

# name, year, is_active, is_locked
# Spring 2027 is the semester being allocated; earlier ones are finished and locked.
SEMESTERS = [
    ("Spring", 2025, False, True),
    ("Fall", 2025, False, True),
    ("Spring", 2026, False, True),
    ("Fall", 2026, False, True),
    ("Spring", 2027, True, False),
]

# How many sections of each course are offered in the semester being allocated.
TARGET_SEMESTER = ("Spring", 2027)
SECTIONS_TO_OFFER = {
    "CS-101": 3, "CS-102": 3, "CS-201": 3, "CS-210": 2, "CS-220": 1,
    "CS-230": 1, "CS-310": 2, "CS-320": 1, "CS-330": 1, "CS-340": 1,
    "CS-350": 1, "CS-360": 1, "CS-370": 1,
    "SE-201": 2, "SE-310": 1, "SE-320": 1, "SE-340": 1,
    "AI-201": 2, "AI-301": 2, "AI-310": 1, "AI-401": 1, "AI-410": 1,
    "AI-420": 1, "AI-430": 1,
}
