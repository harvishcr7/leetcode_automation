import random


class RandomizedSet:

    def __init__(self):
        self.val_to_idx = {}
        self.nums = []

    def insert(self, val: int) -> bool:
        if val in self.val_to_idx:
            return False
        self.val_to_idx[val] = len(self.nums)
        self.nums.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.val_to_idx:
            return False
        idx = self.val_to_idx[val]
        last_elem = self.nums[-1]

        self.nums[idx] = last_elem
        self.val_to_idx[last_elem] = idx

        self.nums.pop()
        del self.val_to_idx[val]
        return True

    def getRandom(self) -> int:
        return random.choice(self.nums)