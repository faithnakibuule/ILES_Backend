DEFAULT_EVALUATION_CRITERIA = [
    {
        "name": "Willingness to Learn",
        "description": (
            "81-100: Learns instantly. Loves feedback. Searches for answers on their own.\n"
            "61-80: Learns fast. Listens well to advice.\n"
            "41-60: Learns at a normal pace. Needs to be told things a few times.\n"
            "21-40: Struggles to understand new tasks. Forgets instructions often.\n"
            "0-20: Shows no interest in learning or improving."
        ),
        "max_score": 100,
        "weight": 0.20,
    },
    {
        "name": "Problem Solving",
        "description": (
            "81-100: Solves tough issues alone. Brings great solutions to the team.\n"
            "61-80: Figures things out with very little help. Think things through.\n"
            "41-60: Can solve normal, everyday tasks. Needs help with hard problems.\n"
            "21-40: Gets stuck easily. Waits for someone to tell them what to do.\n"
            "0-20: Cannot complete tasks without step-by-step hand-holding."
        ),
        "max_score": 100,
        "weight": 0.20,
    },
    {
        "name": "Communication Skills",
        "description": (
            "81-100: Speaks and writes perfectly. Great at updating the team.\n"
            "61-80: Clear and easy to understand. Keeps people informed.\n"
            "41-60: Communicates okay. Sometimes misses details or forgets to reply.\n"
            "21-40: Hard to understand. Emails or updates are messy or late.\n"
            "0-20: Fails to talk to the team. Ignores messages or instructions."
        ),
        "max_score": 100,
        "weight": 0.15,
    },
    {
        "name": "Teamwork",
        "description": (
            "81-100: Inspires others. Everyone loves working with them.\n"
            "61-80: Helpful, polite, and works very well with others.\n"
            "41-60: Gets along with the team. Does their part of the work.\n"
            "21-40: Prefers to work alone. Sometimes causes minor friction.\n"
            "0-20: Difficult to work with. Does not help the team at all."
        ),
        "max_score": 100,
        "weight": 0.15,
    },
    {
        "name": "Reliability",
        "description": (
            "81-100: Never misses a deadline. Always on time. Super dependable.\n"
            "61-80: Reliable. Finishes work on time and arrives on time.\n"
            "41-60: Mostly on time. Misses a deadline occasionally but fixes it.\n"
            "21-40: Often late to work or late finishing tasks. Needs reminders.\n"
            "0-20: Cannot be trusted with tasks. Frequently absent or very late."
        ),
        "max_score": 100,
        "weight": 0.15,
    },
    {
        "name": "Initiative",
        "description": (
            "81-100: Finds extra work to do without asking. Solves problems before they happen.\n"
            "61-80: Asks for more work when finished. Very proactive.\n"
            "41-60: Does exactly what they are told to do. No more, no less.\n"
            "21-40: Needs to be reminded to stay busy. Only does the bare minimum.\n"
            "0-20: Sits idle and waits to be given tasks. Shows no drive."
        ),
        "max_score": 100,
        "weight": 0.15,
    },
]
