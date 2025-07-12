""" Correctly formats a list of maps """
def display_list(data: list[str]):
    return ", ".join(item.capitalize() for item in data)

""" Parses user IDs from a list of Discord Users """
def parse_users(user_str: str) -> list[int]:
    if not user_str:
        return []
    # Split by comma, strip spaces and remove mention syntax
    users = []
    for mention in user_str.split(","):
        mention = mention.strip()
        # Discord mentions look like <@!id> or <@id>, so remove <>
        if mention.startswith("<@") and mention.endswith(">"):
            mention = mention.replace("<@!", "").replace("<@", "").replace(">", "")
        users.append(int(mention))
    return users