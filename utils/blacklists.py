blacklisted_users = set()

def save_blacklist():
    with open("blacklists.txt", "w") as file:
        file.write("\n".join(map(str, blacklisted_users)))

def load_blacklist():
    try:
        with open("blacklists.txt", "r") as file:
            return set(map(int, file.read().splitlines()))
    except FileNotFoundError:
        return set()

blacklisted_users = load_blacklist()

blfile = "blacklistedsv.txt"

def load_blacklistedsv():
    blacklistedsv = set()
    try:
        with open(blfile, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    try:
                        server_id = int(line)
                        blacklistedsv.add(server_id)
                    except ValueError:
                        print("invalid server id")

    except FileNotFoundError:
        print("L")
    except IOError as e:
        print(e)
    return blacklistedsv

def save_blacklistedsv(blacklistedsv):
    try:
        with open(blfile, "w") as file:
            file.write("\n".join(map(str, blacklistedsv)))
    except IOError as e:
        print(e)

blacklistedsv = load_blacklistedsv()