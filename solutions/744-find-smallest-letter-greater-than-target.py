import bisect

class Solution:
    def nextGreatestLetter(self, letters: list[str], target: str) -> str:
        idx = bisect.bisect_right(letters, target)
        return letters[idx % len(letters)]