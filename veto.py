from enum import Enum


class VetoAction(Enum):
    Pick = 1
    Ban = 2


class Veto:
    def __init__(self, channel: int, maps: list[str], team1: list[int], team2: list[int], num_to_select=1):
        self.maps_remaining = maps.copy()
        self.banned_maps = []
        self.picked_maps = []
        self.num_to_select = num_to_select
        self.completed = False

        self.channel = channel

        if num_to_select == 1:
            self.order = [VetoAction.Ban, VetoAction.Ban, VetoAction.Ban, VetoAction.Ban, VetoAction.Ban, VetoAction.Ban]
        elif num_to_select == 3:
            self.order = [VetoAction.Ban, VetoAction.Ban, VetoAction.Pick, VetoAction.Pick, VetoAction.Ban, VetoAction.Ban]
        elif num_to_select == 5:
            self.order = [VetoAction.Ban, VetoAction.Ban, VetoAction.Pick, VetoAction.Pick, VetoAction.Pick, VetoAction.Pick, VetoAction.Pick]

        self._veto_idx = 0
        self.team1 = [int(p) for p in team1]
        self.team2 = [int(p) for p in team2]
        self.active_team = self.team1

    def ban(self, map_to_ban: str, user_id: int):
        """ Bans a map, updates the active team """
        if map_to_ban.lower() in self.maps_remaining:
            self.maps_remaining.remove(map_to_ban.lower())
            self.banned_maps.append(map_to_ban.lower())
            if len(self.maps_remaining) == 1:
                self.picked_maps.append(self.maps_remaining[0])
                self.completed = True
            # If successful, swap team
            if self.active_team == self.team2:
                self.active_team = self.team1
            else:
                self.active_team = self.team2

            self._veto_idx += 1

        elif map_to_ban.lower() in self.banned_maps:
            raise ValueError("Map already banned: " + map_to_ban)
        else:
            raise ValueError("Map not in maps list: " + map_to_ban)

    def pick(self, map_to_pick: str, user_id: int):
        """ Picks a map, updates the active team """
        if map_to_pick.lower() in self.maps_remaining:
            self.maps_remaining.remove(map_to_pick.lower())
            self.picked_maps.append(map_to_pick.lower())
            if len(self.maps_remaining) == 1:
                self.picked_maps.append(self.maps_remaining[0])
                self.completed = True
            # If successful, swap team
            if self.active_team == self.team2:
                self.active_team = self.team1
            else:
                self.active_team = self.team2

            self._veto_idx += 1

        elif map_to_pick.lower() in self.picked_maps:
            raise ValueError("Map already picked: " + map_to_pick)
        else:
            raise ValueError("Map not in maps list: " + map_to_pick)

    def can_user_ban(self, user_id: int):
        """ Returns true if a user is in the active team"""
        return int(user_id) in self.active_team

    def get_veto_action(self):
        """ Returns the current veto action. If veto_idx is greater
        than self.order's len, defaults to ban """
        if self._veto_idx < len(self.order):
            return self.order[self._veto_idx]
        return VetoAction.Ban
