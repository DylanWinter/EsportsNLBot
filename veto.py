class Veto:
    def __init__(self, maps: list[str], team1: list[int], team2: list[int], num_to_select = 1):
        self.maps_remaining = maps.copy()
        self.banned_maps = []
        self.picked_maps = []
        self.num_to_select = num_to_select
        self.completed = False

        self.team1 = [int(p) for p in team1]
        self.team2 = [int(p) for p in team2]
        self.active_team = self.team1

    """ Bans a map, updates the active team """
    def ban(self, map_to_ban: str, user_id: int):
        print(user_id, self.active_team)
        print("active_team:", self.active_team, [type(u) for u in self.active_team])
        print(f"Check: {user_id} in {self.active_team} = {user_id in self.active_team}")
        print(id(self.team1[0]), id(self.active_team[0]))
        if int(user_id) not in self.active_team:
            raise ValueError("User not in banning team.")
        if map_to_ban.lower() in self.maps_remaining:
            self.maps_remaining.remove(map_to_ban.lower())
            self.banned_maps.append(map_to_ban.lower())
            if len(self.maps_remaining) == self.num_to_select:
                self.completed = True
            # If successful, swap team
            if self.active_team == self.team2:
                self.active_team = self.team1
            else:
                self.active_team = self.team2

        elif map_to_ban.lower() in self.banned_maps:
            raise ValueError("Map already banned: "+ map_to_ban)
        else:
            raise ValueError("Map not in maps list: " + map_to_ban)