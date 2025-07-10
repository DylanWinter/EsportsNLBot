class Veto:
    def __init__(self, maps: list[str], num_to_select = 1):
        self.maps_remaining = maps.copy()
        self.banned_maps = []
        self.picked_maps = []
        self.num_to_select = num_to_select
        self.completed = False

    def ban(self, map_to_ban: str):
        print(map_to_ban, map_to_ban.lower())
        if map_to_ban.lower() in self.maps_remaining:
            self.maps_remaining.remove(map_to_ban.lower())
            self.banned_maps.append(map_to_ban.lower())
            if len(self.maps_remaining) == self.num_to_select:
                self.completed = True
        elif map_to_ban.lower() in self.banned_maps:
            raise ValueError("Map already banned: "+ map_to_ban)
        else:
            raise ValueError("Map not in maps list: " + map_to_ban)