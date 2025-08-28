
class WeaponDetector:
    def __init__(self, weapons: list):
        self.weapons = weapons

    def find_weapons(self, text: str) -> list[str] | None:
        list_weapons = []
        for word in text.split():
            if word in self.weapons:
                list_weapons.append(word)
        return list_weapons if len(list_weapons) > 0 else None



if __name__ == "__main__":
    weapons = ["gun", "knife", "rifle"]
    detector = WeaponDetector(weapons)
    text = "He had a gun and a knife"
    print(detector.find_weapons(text))  # Output: ['gun', 'knife']

