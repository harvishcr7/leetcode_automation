class Solution:
    def isSubsequence(self, s: str, t: str) -> bool:
        iterator = iter(t)
        return all(c in iterator for c in s)