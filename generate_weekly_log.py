import os

def create_weekly_log(week_number, start_date, end_date, tasks, tools, notes):
    folder_path = "Logs"
    os.makedirs(folder_path, exist_ok=True)
    log_path = os.path.join(folder_path, f"week{week_number}.md")

    with open(log_path, "w") as f:
        f.write(f"# Internship Log — Week {week_number} ({start_date}–{end_date})\n\n")
        f.write("### Tasks Completed\n")
        for task in tasks:
            f.write(f"- {task}\n")
        f.write("\n### Tools Used\n")
        for tool in tools:
            f.write(f"- {tool}\n")
        f.write("\n### Notes\n")
        f.write(notes + "\n")

    print(f"\nWeek {week_number} log created at {log_path}")

if __name__ == "__main__":
    print("Weekly Log Generator\n")
    
    week_number = input("Enter week number: ")
    start_date = input("Start date: ")
    end_date = input("End date: ")

    print("\nEnter key tasks (type 'done' when finished):")
    tasks = []
    while True:
        task = input("- ")
        if task.lower() == "done":
            break
        tasks.append(task)

    print("\nEnter tools used (type 'done' when finished):")
    tools = []
    while True:
        tool = input("- ")
        if tool.lower() == "done":
            break
        tools.append(tool)

    print("\nEnter notes and reflections:")
    notes = input("> ")

    create_weekly_log(week_number, start_date, end_date, tasks, tools, notes)
