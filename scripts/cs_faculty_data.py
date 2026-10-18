"""
Computer Science faculty, one row per current instructor.

Source: the department's updated faculty list (name + specialization) merged
with the detailed Fall 2025 list (email, academic rank, qualification, status).
Only instructors on the updated list are included; anyone who appears only on
the Fall 2025 list has left and is intentionally left out.

Rows marked "SYNTHETIC details" are not on the detailed list, so their email,
rank, qualification and status are made up (emails use example.com so they can
never collide with a real address). Replace them when real data is available.

Specializations were normalized for consistency (casing, spelling, "AI" ->
"Artificial Intelligence", "IoT" -> "Internet of Things (IoT)") because this
text is what gets turned into an embedding later.

status is "active" or "on_leave" (the type of leave is deliberately not stored).

Columns: name, email, academic_rank, qualification, status, specialization
"""

DEPARTMENT_NAME = "Computer Science"

FACULTY = [
    ("Dr SajidUllah Khan", "sajidullah.khan@example.com", "Assistant Professor", "PhD", "active", "Artificial Intelligence, Computer Vision"),  # SYNTHETIC details
    ("Dr Maria Tariq", "mariatariq@lgu.edu.pk", "Assistant Professor", "PhD", "active", "Machine Learning, Artificial Intelligence"),
    ("Mr Awais Salman Qazi", "awais.salman@lgu.edu.pk", "Senior Lecturer", "MS/M.Phil", "active", "Deep Learning, Information Security, Cooperative Communication, Spectrum Sensing"),
    ("Mr Muhammad Arsalan Raza", "marsalanraza@lgu.edu.pk", "Senior Lecturer", "MS/M.Phil", "active", "Machine Learning, Deep Learning, Natural Language Processing"),
    ("Ms Shan E Zahra", "shanezahra@lgu.edu.pk", "Senior Lecturer", "MS/M.Phil", "active", "Artificial Intelligence"),
    ("Ms Amna Nadeem", "amnanadeem@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence"),
    ("Ms Amna Kosar", "amnakosar@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence"),
    ("Ms Khola Farooq", "kholafarooq@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Machine Learning"),
    ("Ms Sahar Moin", "saharmoin@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Mobile Application Development"),
    ("Ms Tayyaba Sultana", "tayyabasultana@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Deep Learning, Internet of Things (IoT)"),
    ("Mr Mumtaz Ahmad", "cs.mumtaz@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Networking, Web"),
    ("Ms Aisha Riaz", "aishariaz@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Image Processing, Machine Learning, Artificial Intelligence"),
    ("Ms Farwa Javed", "farwajaved@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Machine Learning"),
    ("Ms Rabia Khan", "rabia_khan@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Bioinformatics, Internet of Things (IoT)"),
    ("Ms Ayza Batool", "ayza.batool@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Data Science, Artificial Intelligence, Machine Learning, Natural Language Processing, Cloud Computing"),
    ("Ms Zainab Zafar", "zainabzafar@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Machine Learning"),
    ("Ms Saba Mohsin", "sabamohsin@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Deep Learning"),
    ("Ms Syeda Urwa Warsi", "syedaurwa@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Machine Learning, Deep Learning"),
    ("Ms Fatima Aslam", "fatimaaslam.cs@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Computer Vision"),
    ("Ms Anila Amjad", "anila.amjad@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Machine Learning, Deep Learning, BI, Internet of Things (IoT)"),
    ("Mr Muhammad Zubair", "shzubair@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Game Development, Artificial Intelligence, Machine Learning"),
    ("Ms Nazish Umar Awan", "nazishumar@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Natural Language Processing"),
    ("Mr Umair Bin Ahmad", "umairbinahmad@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Computer Vision, DevOps, Robotics, Embedded Systems, Full Stack Web Development"),
    ("Ms Naila Noreen", "nailanoreen@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Deep Learning"),
    ("Ms Zara Masood", "zaramasood@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Machine Learning, Deep Learning, Artificial Intelligence, Data Science"),
    ("Mr Hamza Shahab Awan", "hamza.awan@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Data Science, Machine Learning, Bioinformatics, Computational Intelligence"),
    ("Mr Saqib Mahmood", "saqib.mahmood@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Image Processing, Computer Vision, Artificial Intelligence"),
    ("Ms Zahra Seemab", "zahraabbas3112@gmail.com", "Lecturer", "MS/M.Phil", "active", "Machine Learning, Deep Learning"),
    ("Ms Tania Saddique", "tania.saddique@lgu.edu.pk", "Lecturer", "MS/M.Phil", "on_leave", "Artificial Intelligence"),
    ("Mr Hassan Abbas Enver", "hassanabbas@lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Machine Learning"),
    ("Mr Hafiz Muhammad Shahid Raza", "malikshahid248@gmail.com", "Lecturer", "MS/M.Phil", "active", "Machine Learning"),
    ("Mr Ahsan Raza", "ahsanraza@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Machine Learning, Deep Learning"),
    ("Ms Khadija Mushtaq Cheema", "khadijacheema@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence, Digital Image Processing"),
    ("Ms Saima Yousaf", "saimayousaf@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Computer Science"),
    ("Ms Rabia Akhtar", "rabiaakhtar@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Software Project Management, Programming, Web Development"),
    ("Ms Ammara Kanwal", "ammarakanwal@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Human-Computer Interaction, Natural Language Processing"),
    ("Mr Masim Ali", "masimali@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Artificial Intelligence"),
    ("Ms Bibi Maryam", "bibimaryam@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Machine Learning"),
    ("Mr Azib Mehmood", "azibmahmood@cs.lgu.edu.pk", "Lecturer", "MS/M.Phil", "active", "Blockchain, Cybersecurity"),
    ("Ms Faria Khan", "faria.khan@example.com", "Lecturer", "MS/M.Phil", "active", "Computer Science"),  # SYNTHETIC details
    ("Mr Awais Nasir", "awais.nasir@example.com", "Assistant Lecturer", "BSCS/MCS", "active", "Programming Subjects"),  # SYNTHETIC details
    ("Mr Umer Ahmed", "umer.ahmad@lgu.edu.pk", "Lecturer", "MS/M.Phil", "on_leave", "Artificial Intelligence, Robotics, Machine Learning, Deep Learning"),
    ("Mr Humayun Majeed", "humayunmajeed@lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Programming Language, Hardware Description Language, Mobile Development"),
    ("Mr Talha Javed", "mtalhajaved@lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Web Development, Database"),
    ("Mr Suhaib Ahmad", "suhaib.ahmad@lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Internet of Things (IoT)"),
    ("Mr Hammad Shoukat", "hammadshoukat78@gmail.com", "Assistant Lecturer", "BSCS/MCS", "active", "Artificial Intelligence, Machine Learning"),
    ("Ms Ayesha Razzaq", "ayesharazzaq@lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Database Systems, Software Quality Assurance"),
    ("Ms Hafsa Tahir", "hafsatahir@cs.lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Web Development"),
    ("Ms Ifra Shahzad", "ifrashshzad@cs.lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Web Development"),
    ("Mr Husnain Ali", "husnainmunir@cs.lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Mobile Application Development, Artificial Intelligence"),
    ("Mr Muhammad Saadat Amir Khan", "muhammadsaadatamirkhan@cs.lgu.edu.pk", "Assistant Lecturer", "BSCS/MCS", "active", "Artificial Intelligence, Machine Learning"),
    ("Mr Amir Sohail", "amir.sohail@example.com", "Assistant Lecturer", "BSCS/MCS", "active", "Web Development"),  # SYNTHETIC details
]
