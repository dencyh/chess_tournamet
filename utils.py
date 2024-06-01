def write_numbers_to_file(num1, num2, file_path):
    with open(file_path, 'a') as file:  # 'a' mode for appending to the file
        file.write(f"{num1} {num2}\n")  # Write numbers with a space and a newline

def read_numbers_from_file(file_path):
    numbers_list = []  # List to hold tuples of numbers
    try:
        with open(file_path, 'r') as file:  # Open file in read mode
            for line in file:  # Read each line in the file
                parts = line.strip().split()  # Split line into parts based on whitespace
                if len(parts) == 2:  # Ensure there are exactly two elements to process
                    num1, num2 = int(parts[0]), int(parts[1])  # Convert strings to integers
                    numbers_list.append(num1)  # Append the tuple to the list
                    numbers_list.append(num2)  # Append the tuple to the list
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except ValueError:
        print("Error converting numbers. Ensure the file contains only pairs of integers.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return numbers_list